
file(
   name = "readme",
   source = "README.md",
)

oras_artifact(
   tag = "foobar",
   name = "test-oras",
   sources = [
      "README.md"
   ],
   dependencies = [":readme"]
)
