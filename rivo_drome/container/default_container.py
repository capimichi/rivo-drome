import logging
import os

from dotenv import load_dotenv
from injector import Injector

from rivo_drome.client.deezer_client import DeezerClient
from rivo_drome.client.example_client import ExampleClient
from rivo_drome.client.jackett_client import JackettClient
from rivo_drome.client.torrserver_client import TorrServerClient
from rivo_drome.config.example_config import ExampleConfig
from rivo_drome.config.navidrome_config import NavidromeConfig
from rivo_drome.command.example_command import ExampleCommand
from rivo_drome.controller.example_controller import ExampleController
from rivo_drome.controller.navidrome_proxy_controller import NavidromeProxyController
from rivo_drome.controller.search_controller import SearchController
from rivo_drome.controller.stream_controller import StreamController
from rivo_drome.factory.example_factory import ExampleFactory
from rivo_drome.generator.example_generator import ExampleGenerator
from rivo_drome.helper.example_helper import ExampleHelper
from rivo_drome.logger.proxy_logger import ProxyLogger
from rivo_drome.manager.db_manager import DbManager
from rivo_drome.manager.example_manager import ExampleManager
from rivo_drome.manager.navidrome_sample_response_manager import NavidromeSampleResponseManager
from rivo_drome.mapper.example_mapper import ExampleMapper
from rivo_drome.orchestrator.example_orchestrator import ExampleOrchestrator
from rivo_drome.prompt.example_prompt import ExamplePrompt
from rivo_drome.repository.artist_repository import ArtistRepository
from rivo_drome.repository.example_repository import ExampleRepository
from rivo_drome.repository.track_repository import TrackRepository
from rivo_drome.service.downloader.base_downloader import BaseDownloader
from rivo_drome.service.downloader.torrent_downloader import TorrentDownloader
from rivo_drome.service.downloader.youtube_downloader import YoutubeDownloader
from rivo_drome.service.example_service import ExampleService
from rivo_drome.service.navidrome_proxy_service import NavidromeProxyService
from rivo_drome.service.stream_service import StreamService


class DefaultContainer:
    """Example dependency container inspired by the coursify layout."""

    injector = None
    instance = None

    @staticmethod
    def getInstance():
        if DefaultContainer.instance is None:
            instance = object.__new__(DefaultContainer)
            DefaultContainer.instance = instance
            instance.__init__()
        return DefaultContainer.instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._initialized = True

        self.injector = Injector()

        load_dotenv()

        self._init_environment_variables()
        self._init_directories()
        self._init_logging()
        self._init_bindings()

    def get(self, key):
        return self.injector.get(key)

    def get_var(self, key: str):
        return self.__dict__[key]

    def _init_directories(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.var_dir = os.path.join(self.root_dir, 'var')
        os.makedirs(self.var_dir, exist_ok=True)
        self.log_dir = os.path.join(self.var_dir, 'log')
        os.makedirs(self.log_dir, exist_ok=True)
        self.app_log_path = os.path.join(self.log_dir, 'app.log')
        self.session_dir = os.path.join(self.root_dir, self.session_dir_env)
        os.makedirs(self.session_dir, exist_ok=True)
        self.download_dir = os.path.join(self.root_dir, self.download_dir_env)
        os.makedirs(self.download_dir, exist_ok=True)

    def _init_environment_variables(self):
        self.app_name = os.environ.get('APP_NAME', 'Example App')
        self.debug = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.default_limit = int(os.environ.get('DEFAULT_LIMIT', '10'))
        self.api_host = os.environ.get('API_HOST', '0.0.0.0')
        self.api_port = int(os.environ.get('API_PORT', '8459'))
        self.session_dir_env = os.environ.get('SESSION_DIR', 'var/session')
        self.navidrome_url = os.environ.get('NAVIDROME_URL', 'http://localhost:4533')
        self.navidrome_music_dir = os.environ.get('NAVIDROME_MUSIC_DIR', '')
        self.db_url = os.environ.get('DB_URL', 'mysql+pymysql://rivodrome:rivodrome@mariadb:3306/rivodrome')
        self.jackett_url = os.environ.get('JACKETT_URL', 'http://localhost:9117')
        self.jackett_api_key = os.environ.get('JACKETT_API_KEY', '')
        self.torrserver_url = os.environ.get('TORRSERVER_URL', 'http://localhost:8090')
        self.downloader_chain_str = os.environ.get('DOWNLOADER_CHAIN', 'torrent,youtube')
        self.download_dir_env = os.environ.get('DOWNLOAD_DIR', 'var/music')

    def _init_logging(self):
        logging.basicConfig(
            filename=self.app_log_path,
            level=logging.DEBUG if self.debug else logging.INFO,
            filemode='a',
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
            datefmt='%H:%M:%S',
        )

    def _init_bindings(self):
        example_config = ExampleConfig(
            app_name=self.app_name,
            debug=self.debug,
            default_limit=self.default_limit,
        )
        self.injector.binder.bind(ExampleConfig, to=example_config)

        example_repository = ExampleRepository()
        self.injector.binder.bind(ExampleRepository, to=example_repository)

        example_manager = ExampleManager(example_repository)
        self.injector.binder.bind(ExampleManager, to=example_manager)

        example_generator = ExampleGenerator()
        self.injector.binder.bind(ExampleGenerator, to=example_generator)

        example_factory = ExampleFactory()
        self.injector.binder.bind(ExampleFactory, to=example_factory)

        example_helper = ExampleHelper()
        self.injector.binder.bind(ExampleHelper, to=example_helper)

        example_mapper = ExampleMapper()
        self.injector.binder.bind(ExampleMapper, to=example_mapper)

        example_prompt = ExamplePrompt()
        self.injector.binder.bind(ExamplePrompt, to=example_prompt)

        example_client = ExampleClient()
        self.injector.binder.bind(ExampleClient, to=example_client)

        example_service = ExampleService(example_client)
        self.injector.binder.bind(ExampleService, to=example_service)

        example_orchestrator = ExampleOrchestrator(example_generator, example_manager)
        self.injector.binder.bind(ExampleOrchestrator, to=example_orchestrator)

        example_controller = ExampleController(example_service)
        self.injector.binder.bind(ExampleController, to=example_controller)

        example_command = ExampleCommand(example_service)
        self.injector.binder.bind(ExampleCommand, to=example_command)

        navidrome_config = NavidromeConfig(
            url=self.navidrome_url,
            music_dir=self.navidrome_music_dir,
        )
        self.injector.binder.bind(NavidromeConfig, to=navidrome_config)

        samples_dir = os.path.join(self.var_dir, 'samples')
        proxy_logger = ProxyLogger(log_dir=self.log_dir)
        self.injector.binder.bind(ProxyLogger, to=proxy_logger)

        navidrome_sample_manager = NavidromeSampleResponseManager(samples_dir=samples_dir)
        self.injector.binder.bind(NavidromeSampleResponseManager, to=navidrome_sample_manager)

        navidrome_proxy_service = NavidromeProxyService(proxy_logger, navidrome_sample_manager, navidrome_config)
        self.injector.binder.bind(NavidromeProxyService, to=navidrome_proxy_service)

        navidrome_proxy_controller = NavidromeProxyController(navidrome_proxy_service)
        self.injector.binder.bind(NavidromeProxyController, to=navidrome_proxy_controller)

        # --- Infrastruttura: binding espliciti solo per classi con parametri letterali ---

        db_manager = DbManager(db_url=self.db_url)
        self.injector.binder.bind(DbManager, to=db_manager)

        jackett_client = JackettClient(jackett_url=self.jackett_url, api_key=self.jackett_api_key)
        self.injector.binder.bind(JackettClient, to=jackett_client)

        torrserver_client = TorrServerClient(torrserver_url=self.torrserver_url)
        self.injector.binder.bind(TorrServerClient, to=torrserver_client)

        chain_order = [s.strip() for s in self.downloader_chain_str.split(",") if s.strip()]
        downloaders = {}
        if "torrent" in chain_order:
            downloaders["torrent"] = TorrentDownloader(jackett_client, torrserver_client)
        if "youtube" in chain_order:
            downloaders["youtube"] = YoutubeDownloader()
        first = None
        prev = None
        for name in chain_order:
            d = downloaders.get(name)
            if d is None:
                continue
            if first is None:
                first = d
                prev = d
            else:
                prev.set_next(d)
                prev = d
        self.injector.binder.bind(BaseDownloader, to=first)

        artist_repo = self.injector.get(ArtistRepository)
        track_repo = self.injector.get(TrackRepository)
        stream_service = StreamService(
            track_repository=track_repo,
            artist_repository=artist_repo,
            downloader_chain=first,
            download_dir=self.download_dir,
        )
        self.injector.binder.bind(StreamService, to=stream_service)

        self._db_manager = db_manager
