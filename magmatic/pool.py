from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Dict, Final, Generic, Iterator, List, Optional, TYPE_CHECKING, TypeVar, Union

from discord import Client
from discord.utils import copy_doc

from .errors import NoAvailableNodes, NoMatches, NodeConflict, PlayerNotFound

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from discord.abc import Snowflake

    from .node import JSONSerializer, Node
    from .player import Player

ClientT = TypeVar('ClientT', bound=Client)

__all__ = (
    'NodePool',
    'DefaultNodePool',
    'add_node',
    'create_node',
    'start_node',
    'get_node',
)


class NodePool(Generic[ClientT]):
    """Represents a pool of Lavalink nodes.

    By default, a default node pool (:ref:`DefaultNodePool`) is created, however
    you can construct these yourself.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}

    @property
    def nodes(self) -> List[Node]:
        """list[:class:`Node`]: A list of nodes in the pool."""
        return list(self.walk_nodes())

    def walk_nodes(self) -> Iterator[Node]:
        """Walks over all nodes in the pool.

        Yields
        ------
        :class:`Node`
            A node in the pool.
        """
        yield from self._nodes.values()

    def add_node(self, node: Node[ClientT], *, identifier: str = None) -> None:
        """Adds an existing node to the pool.

        Parameters
        ----------
        node: :class:`Node`
            The node to add to the pool.
        identifier: Optional[:class:`str`]
            The identifier to use for the node.
            If not specified, the node's :attr:`identifier <.Node.identifier>` will be used.
        """
        if identifier is None:
            identifier = node.identifier

        if identifier in self._nodes:
            raise NodeConflict(self, identifier)

        self._nodes[identifier or node.identifier] = node

    def create_node(
        self,
        *,
        bot: ClientT,
        host: str = '127.0.0.1',
        port: Union[int, str] = 2333,
        password: Optional[str] = None,
        region: Optional[str] = None,
        identifier: Optional[str] = None,
        session: Optional[ClientSession] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        prefer_http: bool = False,
        secure: bool = False,
        serializer: JSONSerializer[Dict[str, Any]] = json,
    ) -> Node[ClientT]:
        """Creates a new :class:`.Node` and adds it to the pool.

        All parameters are keyword only.

        Parameters
        ----------
        bot: :class:`discord.Client`
            The discord.py client/bot instance that this node should be associated with.
        host: :class:`str`
            The host of the Lavalink process.
            In most cases this is an IP address. Defaults to ``'127.0.0.1'``.
        port: :class:`int`
            The port the Lavalink process is listening on. Defaults to ``2333``.
        password: :class:`str`
            The password required to authenticate with Lavalink. Leave blank if no password was set.
        region: :class:`str`
            The voice region of the node. This is solely used to optimially balance nodes.
        identifier: :class:`str`
            The string identifier used to identify this node.

            A completely random identifier will be generated if this is left blank,
            unless if this is the first node in the pool. Then it will default to ``'MAIN'``.
        session: :class:`aiohttp.ClientSession`
            The aiohttp session to use for the node. Leave blank to generate one automatically.
        loop: :class:`asyncio.AbstractEventLoop`
            The event loop to use for the node.

            Leaving this blank will default to your bot's event loop, and as a result
            this method will only work in async-contexts, e.g. in :meth:`setup_hook <discord.Client.setup_hook>`.
        prefer_http: :class:`bool`
            Whether to connect to Lavalink's WebSocket over an HTTP protocol over the standard ``ws`` protocol.
            Defaults to ``False``.
        secure: :class:`bool`
            Whether to use a secure protocol when requesting/connecting to Lavalink.
            Only set this to ``True`` if the given ``host`` is remote.

            Defaults to ``False``.
        serializer
            An object/module with two methods: ``loads`` and ``dumps`` which serializes
            and deserializes JSON data.

            Defaults to the standard :module:`json` module.

        Returns
        -------
        :class:`.Node`
            The created node.

        Raises
        ------
        NodeConflict
            The node identifier is already in use.
        """
        if identifier is None and not self._nodes:
            identifier = 'MAIN'

        if identifier in self._nodes:
            raise NodeConflict(self, identifier)

        node = Node(
            bot=bot,
            host=host,
            port=port,
            password=password,
            region=region,
            identifier=identifier,
            session=session,
            loop=loop,
            prefer_http=prefer_http,
            secure=secure,
            serializer=serializer,
        )
        self._nodes[identifier] = node
        return node

    async def start_node(
        self,
        *,
        bot: ClientT,
        host: str = '127.0.0.1',
        port: Union[int, str] = 2333,
        password: Optional[str] = None,
        region: Optional[str] = None,
        identifier: Optional[str] = None,
        session: Optional[ClientSession] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        prefer_http: bool = False,
        secure: bool = False,
        serializer: JSONSerializer[Dict[str, Any]] = json,
    ) -> Node[ClientT]:
        """|coro|

        Creates a new :class:`.Node`, adds it to the pool, and immediately starts the node.

        All parameters are keyword only.

        Parameters
        ----------
        bot: :class:`discord.Client`
            The discord.py client/bot instance that this node should be associated with.
        host: :class:`str`
            The host of the Lavalink process.
            In most cases this is an IP address. Defaults to ``'127.0.0.1'``.
        port: :class:`int`
            The port the Lavalink process is listening on. Defaults to ``2333``.
        password: :class:`str`
            The password required to authenticate with Lavalink. Leave blank if no password was set.
        region: :class:`str`
            The voice region of the node. This is solely used to optimially balance nodes.
        identifier: :class:`str`
            The string identifier used to identify this node.

            A completely random identifier will be generated if this is left blank,
            unless if this is the first node in the pool. Then it will default to ``'MAIN'``.
        session: :class:`aiohttp.ClientSession`
            The aiohttp session to use for the node. Leave blank to generate one automatically.
        loop: :class:`asyncio.AbstractEventLoop`
            The event loop to use for the node.

            Leaving this blank will default to your bot's event loop, and as a result
            this method will only work in async-contexts, e.g. in :meth:`setup_hook <discord.Client.setup_hook>`.
        prefer_http: :class:`bool`
            Whether to connect to Lavalink's WebSocket over an HTTP protocol over the standard ``ws`` protocol.
            Defaults to ``False``.
        secure: :class:`bool`
            Whether to use a secure protocol when requesting/connecting to Lavalink.
            Only set this to ``True`` if the given ``host`` is remote.

            Defaults to ``False``.
        serializer
            An object/module with two methods: ``loads`` and ``dumps`` which serializes
            and deserializes JSON data.

            Defaults to the standard :module:`json` module.

        Returns
        -------
        :class:`.Node`
            The created node.

        Raises
        ------
        NodeConflict
            The node identifier is already in use.
        """
        node = self.create_node(
            bot=bot,
            host=host,
            port=port,
            password=password,
            region=region,
            identifier=identifier,
            session=session,
            loop=loop,
            prefer_http=prefer_http,
            secure=secure,
            serializer=serializer,
        )
        await node.start()
        return node

    def get_node(self, identifier: Optional[str] = None, *, region: Optional[str] = None) -> Node[ClientT]:
        """Gets the least loaded node from this pool that has the given identifier and/or region.

        Parameters
        ----------
        identifier: :class:`str`
            The string identifier used to identify the node. Leave blank to allow all nodes.
        region: :class:`str`
            The voice region associated with the node. Leave blank to allow all voice regions.

        Returns
        -------
        :class:`.Node`
            The node that was found.

        Raises
        ------
        NoAvailableNodes
            There are no nodes on this node pool.
        NoMatches
            No nodes on this pool match the identifier and/or region.
        """
        if not self._nodes:
            raise NoAvailableNodes(self)

        if identifier is not None:
            try:
                return self._nodes[identifier]
            except KeyError:
                raise NoMatches(self, identifier, region)

        if region is not None:
            nodes = (node for node in self.walk_nodes() if node.region == region)
        else:
            nodes = self.walk_nodes()

        try:
            return sorted(nodes, key=lambda node: node.player_count)[0]
        except IndexError:
            raise NoMatches(self, identifier, region)

    def get_player(self, guild: Snowflake, *, node: Optional[Node[ClientT]] = None) -> Player[ClientT]:
        """Gets the player for the given guild.

        If no player is found, one will be created automatically on the given node.

        Parameters
        ----------
        guild: :class:`int`
            The guild to get the player for.

            Could be a :class:`snowflake <discord.abc.Snowflake>`-like object,
            such as :class:`discord.Object`, if you cannot resolve the full guild object yet.
        node: Optional[:class:`.Node`]
            The node to get the player from.

            If left as ``None``, the node will be determined automatically.

        Returns
        -------
        :class:`.Player`
            The player for the guild.
        """
        if node is None:
            for node in self.walk_nodes():
                try:
                    return node.get_player(guild, fail_if_not_exists=True)
                except PlayerNotFound:
                    continue

            node = self.get_node()

        return node.get_player(guild)

    async def destroy(self) -> None:
        """|coro|

        Clears all nodes from this pool, disconnecting each of them.

        This is useful to be called in :meth:`Client.close <discord.Client.close>`.
        """
        for node in self.walk_nodes():
            await node.destroy()

        self._nodes.clear()

    def __len__(self) -> int:
        return len(self._nodes)


DefaultNodePool: Final[NodePool[Client]] = NodePool()


@copy_doc(NodePool.create_node)
def create_node(
    *,
    bot: ClientT,
    host: str = '127.0.0.1',
    port: Union[int, str] = 2333,
    password: Optional[str] = None,
    region: Optional[str] = None,
    identifier: Optional[str] = None,
    session: Optional[ClientSession] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    prefer_http: bool = False,
    secure: bool = False,
    serializer: JSONSerializer[Dict[str, Any]] = json,
) -> Node[ClientT]:
    return DefaultNodePool.create_node(
        bot=bot,
        host=host,
        port=port,
        password=password,
        region=region,
        identifier=identifier,
        session=session,
        loop=loop,
        prefer_http=prefer_http,
        secure=secure,
        serializer=serializer,
    )


@copy_doc(NodePool.start_node)
def start_node(
    *,
    bot: ClientT,
    host: str = '127.0.0.1',
    port: Union[int, str] = 2333,
    password: Optional[str] = None,
    region: Optional[str] = None,
    identifier: Optional[str] = None,
    session: Optional[ClientSession] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    prefer_http: bool = False,
    secure: bool = False,
    serializer: JSONSerializer[Dict[str, Any]] = json,
) -> Awaitable[Node[ClientT]]:
    return DefaultNodePool.start_node(
        bot=bot,
        host=host,
        port=port,
        password=password,
        region=region,
        identifier=identifier,
        session=session,
        loop=loop,
        prefer_http=prefer_http,
        secure=secure,
        serializer=serializer,
    )


@copy_doc(NodePool.add_node)
def add_node(node: Node[Any], *, identifier: str = None) -> None:
    DefaultNodePool.add_node(node, identifier=identifier)


@copy_doc(NodePool.get_node)
def get_node(identifier: Optional[str] = None, *, region: Optional[str] = None) -> Node[Any]:
    return DefaultNodePool.get_node(identifier=identifier, region=region)


@copy_doc(NodePool.get_player)
def get_player(guild: Snowflake, *, node: Optional[Node[ClientT]] = None) -> Player[ClientT]:
    return DefaultNodePool.get_player(guild, node=node)
