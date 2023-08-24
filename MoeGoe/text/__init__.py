""" from https://github.com/keithito/tacotron """
from . import cleaners



def text_to_sequence(text, symbols, cleaner_names,type=1):
  '''Converts a string of text to a sequence of IDs corresponding to the symbols in the text.
    Args:
      text: string to convert to a sequence
      cleaner_names: names of the cleaner functions to run the text through
    Returns:
      List of integers corresponding to the symbols in the text
  '''
  _symbol_to_id = {s: i for i, s in enumerate(symbols)}
  _id_to_symbol = {i: s for i, s in enumerate(symbols)}
  if type == 1: 

    sequence = []

    clean_text = _clean_text(text, cleaner_names)
    for symbol in clean_text:
      if symbol not in _symbol_to_id.keys():
        continue
      symbol_id = _symbol_to_id[symbol]
      sequence += [symbol_id]
    return sequence
  elif type == 2:
    sequence = []
    clean_text = _clean_text(text, cleaner_names)
    return cleaned_text_to_sequence(clean_text,_symbol_to_id)


def cleaned_text_to_sequence(cleaned_text,_symbol_to_id):
  '''Converts a string of text to a sequence of IDs corresponding to the symbols in the text.
    Args:
      text: string to convert to a sequence
    Returns:
      List of integers corresponding to the symbols in the text
  '''
  sequence = []
  for symbol in cleaned_text.split(" "):
    if symbol in _symbol_to_id:
      sequence.append(_symbol_to_id[symbol])
    else:
      for s in symbol:
        sequence.append(_symbol_to_id[s])
    sequence.append(_symbol_to_id[" "])
  if sequence[-1] == _symbol_to_id[" "]:
    sequence = sequence[:-1]
  return sequence


def sequence_to_text(sequence,_id_to_symbol):
  '''Converts a sequence of IDs back to a string'''
  result = ''
  for symbol_id in sequence:
    s = _id_to_symbol[symbol_id]
    result += s
  return result

def _clean_text(text, cleaner_names):
  for name in cleaner_names:
    cleaner = getattr(cleaners, name)
    if not cleaner:
      raise Exception('Unknown cleaner: %s' % name)
    text = cleaner(text)
  return text
