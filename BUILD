
oras_artifact(
   name = "test-oras",
   repository = "hello-from-pants",
   artifact_type = "application/vnd.me.pants-test",
   layers = {
      "README.md": "text/markdown",
   },
   annotations = {
      "buildtool": "pantsbuild",
   }
)

oras_attachment(
   name = "test-oras-attach",
   repository = "hello-from-pants",
   artifact_type = "application/vnd.me.pants-test.checksum",
   layers = {
      "sum": "text/plain",
   },
   annotations = {
      "buildtool": "pantsbuild",
   },
   dependencies = [
      ":test-oras",
   ],
)
