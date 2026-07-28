import orjson
from typing import Union, List, Optional, Any
from urllib.parse import urlparse
from .tools import Permission, PolicyCapability, PolicyKeyspaceType, SemanticModel, PolicyFormat
from .utils import send_data

class Engine:
    """
    Represents the configuration and connection details for a communication engine.

    Attributes:
        host (str): The hostname or IP address of the server to connect to.
        port (int): The port number on the server to use for the connection.
        username (str): The username for authentication with the server.
        password (str): The password for authentication with the server.
        store (str): The name of the data store on the server.
    """
    VALID_PERMISSIONS = {'read', 'write', 'all'}

    def __init__(self, host: str, port: int, username: str, password: str, store: Union[str, None] = None, tls: bool = False) -> None:
        """
        Initializes the Engine with the given connection parameters.

        Args:
            host (str): Hostname or IP address of the server.
            port (int): Port number to connect to.
            username (str): Username for server authentication.
            password (str): Password for server authentication.
            store (str): Name of the data store to interact with.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.store = store
        self.tls = tls

    @classmethod
    def from_uri(cls, uri: str) -> 'Engine':
        """
        Creates an Engine instance from a URI string in the format:
        montycat://username:password@host:port[/store]

        The store is optional. If not provided, it will be set to None.

        Args:
            uri (str): The URI string to parse.

        Returns:
            Engine: An instance of Engine with the parsed parameters.

        Raises:
            ValueError: If the URI is invalid, has incorrect format, or cannot be parsed.
        """
        if not uri.startswith("montycat://"):
            raise ValueError("URI must use 'montycat://' protocol")

        parsed = urlparse(uri)

        if not parsed.username or not parsed.password:
            raise ValueError("Username and password must be provided")
        if not parsed.hostname or not parsed.port:
            raise ValueError("Host and port must be provided")

        # Optional store
        store = parsed.path[1:] if parsed.path and len(parsed.path) > 1 else None

        return cls(
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            store=store
        )

    async def _execute_query_with_credentials(self, command: List[Any]) -> Any:
        """
        Executes a command query asynchronously.

        Args:
            command (List[Any]): The command to be executed on the server.

        Returns:
            Any: The server's response after executing the command.
        """
        query = orjson.dumps({
            "raw": command,
            "credentials": [self.username, self.password]
        })
        return await send_data(self.host, self.port, query, tls=self.tls)

    async def create_store(self) -> Any:
        """
        Creates a new data store on the server.

        Args:
            persistent (bool): Flag indicating if the store should be persistent.

        Returns:
            bool
        """
        return await self._execute_query_with_credentials([
            'create-store', "store", self.store
        ])

    async def remove_store(self) -> Any:
        """
        Removes an existing data store from the server.

        Args:
            persistent (bool): Flag indicating if the removal should be persistent.

        Returns:
            bool
        """
        return await self._execute_query_with_credentials([
            'remove-store', "store", self.store
        ])

    async def grant_to(self, owner: str, permission: Union[str, Permission], keyspaces: Optional[Union[List[str], str, None]] = None) -> Any:
        """
        Grants specific permissions to a user for the current store.

        Args:
            owner (str): The user to grant permissions to.
            permission (str): The type of permission ('read', 'write', 'all').
            keyspaces (Optional[Union[List[str], str]]): Optional keyspaces for permission scoping.

        Returns:
            bool

        Raises:
            ValueError: If an invalid permission is provided.
        """
        normalized_permission = str(permission).strip().lower()
        if normalized_permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {self.VALID_PERMISSIONS}")

        command = ['grant-to', "owner", owner, "permission", normalized_permission, "store", self.store]
        if keyspaces:
            command.append("keyspaces")
            if isinstance(keyspaces, str):
                command.append(keyspaces)
            else:
                command.extend(keyspaces)

        return await self._execute_query_with_credentials(command)

    async def revoke_from(self, owner: str, permission: Union[str, Permission], keyspaces: Optional[Union[List[str], str]] = None) -> Any:
        """
        Revokes specific permissions from a user for the current store.

        Args:
            owner (str): The user to revoke permissions from.
            permission (str): The type of permission ('read', 'write', 'all').
            keyspaces (Optional[Union[List[str], str]]): Optional keyspaces for permission scoping.

        Returns:
            bool

        Raises:
            ValueError: If an invalid permission is provided.
        """
        normalized_permission = str(permission).strip().lower()
        if normalized_permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {self.VALID_PERMISSIONS}")

        command = ['revoke-from', "owner", owner, "permission", normalized_permission, "store", self.store]
        if keyspaces:
            command.append("keyspaces")
            if isinstance(keyspaces, str):
                command.append(keyspaces)
            else:
                command.extend(keyspaces)

        return await self._execute_query_with_credentials(command)

    async def create_owner(self, owner: str, password: str) -> Any:
        """
        Creates a new owner on the server with specified credentials.

        Args:
            owner (str): The username for the new owner.
            password (str): The password for the new owner.

        Returns:
            bool
        """
        return await self._execute_query_with_credentials([
            'create-owner', "username", owner, "password", password
        ])

    async def remove_owner(self, owner: str) -> Any:
        """
        Removes an owner from the server.

        Args:
            owner (str): The username of the owner to be removed.

        Returns:
            bool
        """
        return await self._execute_query_with_credentials([
            'remove-owner', "username", owner
        ])

    async def list_owners(self) -> Any:
        """
        Lists all owners registered on the server.

        Returns:
            Any: The server's response containing the list of owners.
        """
        return await self._execute_query_with_credentials(['list-owners'])

    async def enable_semantic_search(self, model: Optional[SemanticModel] = None, field: Union[str, None] = None, store: Union[str, None] = None, keyspace: Union[str, None] = None) -> Any:
        """
        Enable semantic (vector similarity) search.

        Without `store`, this is DB-wide: it flips the whole database on, sets the default
        embedding model and field, and enrolls every existing keyspace that has no semantic
        config yet (each gets a background backfill so its existing items become searchable).
        The chosen model is downloaded on demand on first enable, so this call may take a
        while the first time.

        With `store`, it is scoped: only that store's un-enrolled keyspaces are enrolled and
        backfilled; the DB-wide switch and default model/field are left untouched. Use this
        to (re-)enable one store without re-embedding the entire database.

        Args:
            model (str, optional): The embedding model key to use by default. One of
                                   'minilm', 'bge-small', 'bge-base', 'e5-small'. Default
                                   None, which uses the server default ('bge-small').
            field (str, optional): The JSON field of each value to embed. Default None,
                                   which embeds the whole value.
            store (str, optional): Restrict enrollment/backfill to this store only. Default
                                   None (DB-wide). If the DB-wide switch is off, a scoped
                                   enable enrolls but nothing embeds until a DB-wide enable.

        Returns:
            Any: The server's response describing the enabled model and enrolled keyspaces.
        """
        if keyspace and not store:
            raise ValueError("A store is required when keyspace is specified")
        command = ['enable-semantic-search']
        if model:
            command.extend(["model", model.value])
        if field:
            command.extend(["field", field])
        if store:
            command.extend(["store", store])
        if keyspace:
            command.extend(["keyspace", keyspace])

        return await self._execute_query_with_credentials(command)

    async def disable_semantic_search(self, drop_vectors: bool = False, store: Union[str, None] = None, keyspace: Union[str, None] = None) -> Any:
        """
        Disable semantic search.

        Without `store`, this is DB-wide: embedding and semantic queries stop across the
        whole database; stored vectors are kept by default so re-enabling resumes without
        a full re-embed.

        With `store`, it is scoped: only that store's keyspaces are unenrolled (their
        configs and resident graphs dropped); the DB-wide switch and all other stores are
        left untouched. This is the surgical way to reset one store's semantic state
        instead of nuking and re-backfilling the whole database.

        Args:
            drop_vectors (bool, optional): If True, also clear stored vectors — every
                                           keyspace's DB-wide, or the scoped store's when
                                           `store` is set. Required before switching to a
                                           different embedding model. Default False.
            store (str, optional): Restrict the disable to this store only. Default None
                                   (DB-wide).

        Returns:
            Any: The server's response confirming the disable.
        """
        if keyspace and not store:
            raise ValueError("A store is required when keyspace is specified")
        command = ['disable-semantic-search']
        if drop_vectors:
            command.append("drop-vectors")
        if store:
            command.extend(["store", store])
        if keyspace:
            command.extend(["keyspace", keyspace])

        return await self._execute_query_with_credentials(command)

    async def policy_view(self, owner: Optional[str] = None, store: Optional[str] = None) -> Any:
        command = ['policy-view']
        if owner:
            command.extend(['owner', owner])
        if store:
            command.extend(['store', store])
        return await self._execute_query_with_credentials(command)

    async def policy_history(self, owner: Optional[str] = None, store: Optional[str] = None, keyspace: Optional[str] = None) -> Any:
        command = ['policy-history']
        if owner:
            command.extend(['owner', owner])
        if store:
            command.extend(['store', store])
        if keyspace:
            command.extend(['keyspace', keyspace])
        return await self._execute_query_with_credentials(command)

    async def policy_explain(self, capability: PolicyCapability, store: str, owner: Optional[str] = None, keyspace: Optional[str] = None, keyspace_type: Optional[PolicyKeyspaceType] = None, model: Optional[SemanticModel] = None) -> Any:
        if keyspace_type and capability is PolicyCapability.MANAGE_SNAPSHOTS:
            raise ValueError("keyspace_type is not valid for manage-snapshots policies; snapshots are always in-memory")
        if model and capability not in (
            PolicyCapability.PROVISION_KEYSPACE,
            PolicyCapability.MANAGE_SEMANTIC,
        ):
            raise ValueError("model is only valid for provision-keyspace or manage-semantic policies")
        command = ['policy-explain', 'capability', capability.value, 'store', store]
        if owner:
            command.extend(['owner', owner])
        if keyspace and capability is not PolicyCapability.PROVISION_KEYSPACE:
            command.extend(['keyspace', keyspace])
        if keyspace_type:
            command.extend(['type', keyspace_type.value])
        if model:
            command.extend(['model', model.value])
        return await self._execute_query_with_credentials(command)

    async def _policy_mutation(self, operation: str, owner: str, capability: PolicyCapability, store: str, keyspace: Optional[str] = None, types: Optional[List[PolicyKeyspaceType]] = None, models: Optional[List[SemanticModel]] = None) -> Any:
        if types and capability is PolicyCapability.MANAGE_SNAPSHOTS:
            raise ValueError("types is not valid for manage-snapshots policies; snapshots are always in-memory")
        if models and capability not in (
            PolicyCapability.PROVISION_KEYSPACE,
            PolicyCapability.MANAGE_SEMANTIC,
        ):
            raise ValueError("models is only valid for provision-keyspace or manage-semantic policies")
        command = [operation, 'owner', owner, 'capability', capability.value, 'store', store]
        if keyspace and capability is not PolicyCapability.PROVISION_KEYSPACE:
            command.extend(['keyspace', keyspace])
        if types:
            command.extend(['types', *(keyspace_type.value for keyspace_type in types)])
        if models:
            command.extend(['models', *(model.value for model in models)])
        return await self._execute_query_with_credentials(command)

    async def policy_grant(self, owner: str, capability: PolicyCapability, store: str, keyspace: Optional[str] = None, types: Optional[List[PolicyKeyspaceType]] = None, models: Optional[List[SemanticModel]] = None) -> Any:
        return await self._policy_mutation('policy-grant', owner, capability, store, keyspace, types, models)

    async def policy_revoke(self, owner: str, capability: PolicyCapability, store: str, keyspace: Optional[str] = None, types: Optional[List[PolicyKeyspaceType]] = None, models: Optional[List[SemanticModel]] = None) -> Any:
        return await self._policy_mutation('policy-revoke', owner, capability, store, keyspace, types, models)

    async def policy_deny(self, owner: str, capability: PolicyCapability, store: str, keyspace: Optional[str] = None, types: Optional[List[PolicyKeyspaceType]] = None, models: Optional[List[SemanticModel]] = None) -> Any:
        return await self._policy_mutation('policy-deny', owner, capability, store, keyspace, types, models)

    async def policy_remove_denial(self, owner: str, capability: PolicyCapability, store: str, keyspace: Optional[str] = None, types: Optional[List[PolicyKeyspaceType]] = None, models: Optional[List[SemanticModel]] = None) -> Any:
        return await self._policy_mutation('policy-remove-denial', owner, capability, store, keyspace, types, models)

    async def policy_preview_grant(self, owner: str, capability: PolicyCapability, store: str, keyspace: Optional[str] = None, types: Optional[List[PolicyKeyspaceType]] = None, models: Optional[List[SemanticModel]] = None) -> Any:
        return await self._policy_mutation('policy-preview-grant', owner, capability, store, keyspace, types, models)

    async def policy_preview_revoke(self, owner: str, capability: PolicyCapability, store: str, keyspace: Optional[str] = None, types: Optional[List[PolicyKeyspaceType]] = None, models: Optional[List[SemanticModel]] = None) -> Any:
        return await self._policy_mutation('policy-preview-revoke', owner, capability, store, keyspace, types, models)

    async def _policy_manifest(self, operation: str, document: str, format: PolicyFormat = PolicyFormat.JSON) -> Any:
        return await self._execute_query_with_credentials([operation, 'format', format.value, 'document', document])

    async def policy_validate(self, document: str, format: PolicyFormat = PolicyFormat.JSON) -> Any:
        return await self._policy_manifest('policy-validate', document, format)

    async def policy_plan(self, document: str, format: PolicyFormat = PolicyFormat.JSON) -> Any:
        return await self._policy_manifest('policy-plan', document, format)

    async def policy_apply(self, document: str, format: PolicyFormat = PolicyFormat.JSON) -> Any:
        return await self._policy_manifest('policy-apply', document, format)

    async def policy_export(self, format: PolicyFormat = PolicyFormat.JSON) -> Any:
        return await self._execute_query_with_credentials(['policy-export', 'format', format.value])

    async def get_structure_available(self) -> Any:
        """
        Retrieves the structure of the current store.

        Returns:
            Any: The server's response containing the store structure.
        """

        command = ['get-structure-available', "store", self.store] if self.store else ['get-structure-available']

        return await self._execute_query_with_credentials(command)

    async def enable_wait_for_index(self) -> Any:
        """
        Enable the DB-wide "wait for index" default: writes block until their
        secondary indexes are updated before returning, so a write is
        immediately visible to index-backed reads (e.g. lookup_*_where) at the
        cost of higher write latency.

        Requires superowner credentials.

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['enable-wait-for-index'])

    async def disable_wait_for_index(self) -> Any:
        """
        Disable the DB-wide "wait for index" default: writes return as soon as
        the data is committed and indexing happens asynchronously in the
        background (lower write latency; index-backed reads may briefly lag).
        This is the default behavior.

        Requires superowner credentials.

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['disable-wait-for-index'])

    async def enable_reports(self) -> Any:
        """
        Enable server-side operation reporting (logging). Requires superowner credentials.

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['enable-reports'])

    async def disable_reports(self) -> Any:
        """
        Disable server-side operation reporting (logging). Requires superowner credentials.

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['disable-reports'])

    async def allow_subscriptions(self) -> Any:
        """
        Allow clients to open keyspace subscriptions DB-wide. Requires superowner credentials.

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['allow-subscriptions'])

    async def restrict_subscriptions(self) -> Any:
        """
        Restrict (disallow) keyspace subscriptions DB-wide. Requires superowner credentials.

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['restrict-subscriptions'])

    async def queue_depths(self) -> Any:
        """
        Sample the current depth of every background task queue (index, timer,
        counting) — an observability probe for whether the background runners
        are keeping up with the write rate. Requires superowner credentials.

        Returns:
            Any: The server's response whose payload maps
                 "index" | "timer" | "counting" to per-queue depth maps.
        """
        return await self._execute_query_with_credentials(['queue-depths'])

    async def set_snapshot_rate(self, rate: int) -> Any:
        """
        Set the server-wide snapshot rate. Requires superowner credentials.

        Args:
            rate (int): The snapshot rate value (server-defined units).

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['snapshot-rate', str(rate)])

    async def set_expiration_check_rate(self, rate: int) -> Any:
        """
        Set how often the server scans for expired keys. Requires superowner credentials.

        Args:
            rate (int): The check period in whole seconds (e.g. rate=10 → a scan
                        every 10 seconds). Stored as-is, like the snapshot rate.
                        Defaults to 1 second server-side.

        Returns:
            Any: The server's response confirming the change.
        """
        return await self._execute_query_with_credentials(['expiration-check', str(rate)])
