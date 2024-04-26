import uuid
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Any, Callable, Union, Type, Awaitable

from nestipy_ioc import ModuleProviderDict
from nestipy_metadata import ModuleMetadata, Reflect

T = TypeVar('T')


@dataclass
class DynamicModule:
    module: Any
    exports: list = None
    imports: list = None
    providers: list = None
    controllers: list = None
    is_global: bool = False


class ConfigurableModuleBuilder(Generic[T]):
    def __init__(self):
        self._method_name = 'register'

    def set_method(self, name: str):
        self._method_name = name
        return self

    @classmethod
    def _create_dynamic_module(cls, obj: Any, provider: list) -> DynamicModule:
        return DynamicModule(
            obj,
            providers=provider + Reflect.get_metadata(obj, ModuleMetadata.Providers, []),
            exports=Reflect.get_metadata(obj, ModuleMetadata.Exports, []),
            imports=Reflect.get_metadata(obj, ModuleMetadata.Imports, []),
            controllers=Reflect.get_metadata(obj, ModuleMetadata.Controllers, []),
            is_global=Reflect.get_metadata(obj, ModuleMetadata.Global, False)
        )

    def build(self):
        MODULE_OPTION_TOKEN = f"{uuid.uuid4().hex}_TOKEN"

        def register(cls_: Any, options: Optional[T]) -> DynamicModule:
            provider = ModuleProviderDict(
                token=MODULE_OPTION_TOKEN,
                value=options
            )
            return self._create_dynamic_module(cls_, [provider])

        def register_async(
                cls_: Any,
                value: Any = None,
                factory: Callable[..., Union[Awaitable, Any]] = None,
                existing: Union[Type, str] = None,
                use_class: Type = None,
                inject: list = None
        ) -> DynamicModule:
            provider = ModuleProviderDict(
                token=MODULE_OPTION_TOKEN,
                factory=factory,
                inject=inject or [],
                use_class=use_class,
                existing=existing,
                value=value
            )
            return self._create_dynamic_module(cls_, [provider])

        cls = type('ConfigurableModuleClass', (object,), {
            self._method_name: classmethod(register),
            f"{self._method_name}_async": classmethod(register_async)
        })
        return cls, MODULE_OPTION_TOKEN
