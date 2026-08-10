def build_summary(concepts):
  summary = {}

  for name, concept in concepts.items():
      observations = concept.get("observations", [])

      if not observations:
          continue

      values = [
          observation.get("value")
          for observation in observations
      ]

      summary[name] = {
          "label": concept.get("label", name),
          "domain": concept.get("domain"),
          "values": values
      }

  return summary