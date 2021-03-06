from .dependencies import *
from SourceIO2.source2.data_types.blocks import BaseBlock
from SourceIO2.source2.resource_types.resource import ICompiledResource
from SourceIO2.utils import IBuffer
from SourceIO2.source2.data_types.keyvalues3.binary_keyvalues import BinaryKeyValues


class ResourceEditInfo(BaseBlock):
    def __init__(self, buffer: IBuffer, resource: ICompiledResource):
        super().__init__(buffer, resource)
        self.inputs = InputDependencies()
        self.additional_inputs = AdditionalInputDependencies()
        self.arguments = ArgumentDependencies()
        self.special_deps = SpecialDependencies()
        self.custom_deps = CustomDependencies()
        self.additional_files = AdditionalRelatedFiles()
        self.child_resources = ChildResources()
        self.extra_ints = ExtraInts()
        self.extra_floats = ExtraFloats()
        self.extra_strings = ExtraStrings()

    def __str__(self) -> str:
        return f"<Resource edit info:" \
               f" inputs:{len(self.inputs)}," \
               f" arguments:{len(self.arguments)}," \
               f" child resources:{len(self.child_resources)}>"

    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource):
        self = cls(buffer, resource)
        self.inputs = InputDependencies.from_file(buffer)
        self.additional_inputs = AdditionalInputDependencies.from_file(buffer)
        self.arguments = ArgumentDependencies.from_file(buffer)
        self.special_deps = SpecialDependencies.from_file(buffer)
        self.custom_deps = CustomDependencies.from_file(buffer)
        self.additional_files = AdditionalRelatedFiles.from_file(buffer)
        self.child_resources = ChildResources.from_file(buffer)
        self.extra_ints = ExtraInts.from_file(buffer)
        self.extra_floats = ExtraFloats.from_file(buffer)
        self.extra_strings = ExtraStrings.from_file(buffer)
        return self


class ResourceEditInfo2(ResourceEditInfo):
    @classmethod
    def from_file(cls, buffer: IBuffer, resource: ICompiledResource):
        vkv = BinaryKeyValues.from_file(buffer).root
        self = cls(buffer, resource)
        self.inputs = InputDependencies.from_vkv3(vkv['m_InputDependencies'])
        self.additional_inputs = AdditionalInputDependencies.from_vkv3(vkv['m_AdditionalInputDependencies'])
        self.arguments = ArgumentDependencies.from_vkv3(vkv['m_ArgumentDependencies'])
        self.special_deps = SpecialDependencies.from_vkv3(vkv['m_SpecialDependencies'])
        # self.custom_deps = CustomDependencies.from_vkv3(vkv)
        self.additional_files = AdditionalRelatedFiles.from_vkv3(vkv['m_AdditionalRelatedFiles'])
        self.child_resources = ChildResources.from_vkv3(vkv['m_ChildResourceList'])
        # self.extra_ints = ExtraInts.from_vkv3(vkv)
        # self.extra_floats = ExtraFloats.from_vkv3(vkv)
        # self.extra_strings = ExtraStrings.from_vkv3(vkv)
        return self