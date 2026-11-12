from nomad.config.models.plugins import SchemaPackageEntryPoint


class StandardsSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_pv_stability_standards.schema_packages.standard import m_package

        return m_package


schema_package_entry_point = StandardsSchemaPackageEntryPoint(
    name='StabilityStandards',
    description='PV stability standards, such as the ISOS protocols, as entries.',
)
