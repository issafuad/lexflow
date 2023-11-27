from transformers import LogitsProcessor
import torch
from collections import defaultdict

import torch


class CustomLogitsProcessor(LogitsProcessor):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # Get specific token ids from the dummy function
        specific_token_ids = self.get_specific_token_ids(input_ids)

        # Modify the scores here according to your custom function
        # For now, we just select the scores for the specific token ids
        specific_scores = scores[:, specific_token_ids]

        return specific_scores

    def get_specific_token_ids(self, input_ids):
        # Dummy function that returns a fixed set of token ids
        # Replace this with the actual logic later
        return [1, 2, 3]  # Example token ids

# https://www.bbc.com/news/uk-politics-67420331
def read_document(file_path):
    """
    Reads and returns the contents of a text file.

    Parameters:
    file_path (str): The path to the text file to be read.

    Returns:
    str: The contents of the file.
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return str(e)

def build_word_graph(document):
    # Using defaultdict to automatically handle missing keys
    graph = defaultdict(set)
    previous_word = None
    # Loop over each word in the document
    for word in document.split():
        # Skip adding the first word to any previous word
        if previous_word is not None:
            # Add the word to the set of words that come after the previous word
            graph[previous_word].add(word)
        previous_word = word  # Update the previous word
    return graph


class TrieNode:
    def __init__(self):
        self.children = defaultdict(TrieNode)
        self.next_ids = defaultdict(int)  # Stores next words and their frequencies


class TrieIndex:
    def __init__(self, tokens_list):
        self.root = TrieNode()
        self._insert(tokens_list)

    def _insert(self, tokens):
        # Insert all subsequences of tokens into the trie
        for i in range(len(tokens)):
            current = self.root
            for j in range(i, len(tokens)):
                current = current.children[tokens[j]]
                if j + 1 < len(tokens):
                    current.next_ids[tokens[j + 1]] += 1  # Increment the count of the next word

    def search_next_ids(self, sequence):
        # Find the next possible words after the sequence of tokens
        current = self.root
        for token in sequence:
            if token not in current.children:
                return {}  # If the sequence is not found, return an empty dictionary
            current = current.children[token]

        # Return the next words and their frequencies
        return current.next_ids


class DocumentIndex:
    def __init__(self, document_list, tokenizer):
        self.document_list = document_list
        self.tokenizer = tokenizer
        self.trie_index = TrieIndex(self.get_ids_list())

    def get_ids_list(self):
        all_ids = list()
        # this for now just concatneates all documents together
        # at some point the index should have metadata indicating which document the sequence came from
        for document in self.document_list:
            all_ids.extend(self.tokenizer.encode(document))
        return all_ids

    def get_next_words(self, word_sequence):
        # convert word seuqence to ids
        id_sequence = self.tokenizer.encode(word_sequence)
        # get next ids
        next_ids = self.trie_index.search_next_ids(id_sequence)
        # convert next_ids from default dict to normal dict
        next_ids = dict(next_ids)

        # convert next ids adn their frequencies to next words and their frequencies
        next_words = {self.tokenizer.decode([next_id]): freq for next_id, freq in next_ids.items()}
        # this used ot return the token in teh tokenizer format
        # next_words = self.tokenizer.convert_ids_to_tokens(list(next_ids.keys()))

        #use decode to show the full text of the previous words and the next word
        # return a list of all possible text sequences
        full_text_list = [self.tokenizer.decode(id_sequence + [next_id]) for next_id in next_ids.keys()]
        # put all next_words, next_ids, full_text_list in dictionary and return it
        return {"next_words": next_words, "next_ids": next_ids, "full_text_list": full_text_list}








# tokenizers
# # this gives both attention masks and ids
# # ids = tokenizer(document)# , return_tensors='pt'
# # this just gives ids
# ids = tokenizer.encode(document)
# # this returns the tokens not the ids .
# # tokens = tokenizer.tokenize(document)
# # this returns the full text
# full_text = tokenizer.decode(ids)
# #this converts
# tokens = tokenizer.convert_ids_to_tokens(ids)
#
# ids


# TODO
# look ahead decoding