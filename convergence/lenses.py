def _values(inputs):
  result = {}

  for key, item in inputs.items():
      observations = item.get("observations", [])

      result[key] = [
          observation.get("value")
          for observation in observations
          if observation.get("value") is not None
      ]

  return result


def _mean(values):
  numbers = [
      value
      for value in values
      if isinstance(value, (int, float))
  ]

  if not numbers:
      return None

  return sum(numbers) / len(numbers)


def _base_interpretation(inputs):
  values = _values(inputs)

  humidity = _mean(values.get("atmospheric_moisture", []))
  temperature = _mean(values.get("temperature", []))
  pressure = _mean(values.get("pressure", []))
  cloud = _mean(values.get("cloud", []))
  precipitation = _mean(values.get("precipitation", []))
  vegetation = _mean(values.get("vegetation", []))

  signals = []

  if humidity is not None:
      if humidity >= 80:
          signals.append("high atmospheric moisture")
      elif humidity <= 30:
          signals.append("low atmospheric moisture")

  if temperature is not None:
      if temperature <= 10:
          signals.append("cool thermal conditions")
      elif temperature >= 30:
          signals.append("warm thermal conditions")

  if pressure is not None:
      if pressure < 1000:
          signals.append("relatively low atmospheric pressure")
      elif pressure > 1020:
          signals.append("relatively high atmospheric pressure")

  if cloud is not None:
      if cloud >= 70:
          signals.append("substantial cloud cover")
      elif cloud <= 20:
          signals.append("limited cloud cover")

  if precipitation is not None:
      if precipitation > 0:
          signals.append("active precipitation")
      else:
          signals.append("no recorded precipitation")

  if vegetation is not None:
      if vegetation >= 0.5:
          signals.append("strong vegetation signal")
      else:
          signals.append("moderate or limited vegetation signal")

  if not signals:
      return "No interpretable environmental signals were available."

  return "; ".join(signals) + "."


def _make_lens(name, tradition, lens_type):
  def interpret(inputs):
      return {
          "name": name,
          "tradition": tradition,
          "type": lens_type,
          "interpretation": _base_interpretation(inputs),
      }

  return interpret


astrology = _make_lens(
  "Astrology",
  "Western astrological tradition",
  "symbolic",
)

islamic_cosmology = _make_lens(
  "Islamic Cosmology",
  "Islamic cosmological thought",
  "religious",
)

islamic_mysticism = _make_lens(
  "Islamic Mysticism",
  "Islamic mystical traditions",
  "mystical",
)

christian_mysticism = _make_lens(
  "Christian Mysticism",
  "Christian mystical traditions",
  "religious_mystical",
)

jewish_mysticism = _make_lens(
  "Jewish Mysticism",
  "Jewish mystical traditions",
  "religious_mystical",
)

hindu_cosmology = _make_lens(
  "Hindu Cosmology",
  "Hindu philosophical and cosmological traditions",
  "religious",
)

buddhist_cosmology = _make_lens(
  "Buddhist Cosmology",
  "Buddhist philosophical and cosmological traditions",
  "religious",
)

taoist_cosmology = _make_lens(
  "Taoist Cosmology",
  "Taoist philosophical traditions",
  "philosophical",
)

pagan_wiccan = _make_lens(
  "Pagan / Wiccan",
  "Pagan and Wiccan traditions",
  "earth_spiritual",
)

philosophy = _make_lens(
  "Philosophy",
  "Philosophical traditions",
  "philosophical",
)

psychology = _make_lens(
  "Psychology",
  "Modern psychological frameworks",
  "psychological",
)

esotericism = _make_lens(
  "Western Esotericism",
  "Western esoteric traditions",
  "esoteric",
)