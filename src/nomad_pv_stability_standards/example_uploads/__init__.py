from nomad.config.models.plugins import ExampleUploadEntryPoint

example_upload_entry_point = ExampleUploadEntryPoint(
    title='PV stability standards (ISOS)',
    category='Reference data',
    description='The ISOS stability protocols for perovskite solar cells (Khenkin et '
    'al., Nature Energy 5, 35-49, 2020) as standard entries: every protocol of Table 1 '
    'and the inert protocols of Table 2, with one entry per variant. Publish it once '
    'to give everyone the same standards to reference.',
    resources=['example_uploads/isos/*'],
)
