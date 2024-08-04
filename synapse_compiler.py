import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
import json
import os
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tree import Tree

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

grammar_rules = load_json('grammar_rules.json')
synapse_dictionary = load_json('synapse_dictionary.json')
pattern_matching = load_json('pattern_matching.json')

class SynapseTranslator:
    def __init__(self, master):
        self.master = master
        master.title("Advanced English-Synapse Translator")
        master.geometry("1000x800")

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.translator_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.translator_frame, text="Translator")

        self.explanation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.explanation_frame, text="Synapse Explanation")

        self.setup_translator_tab()
        self.setup_explanation_tab()

    def setup_translator_tab(self):
        input_frame = ttk.LabelFrame(self.translator_frame, text="Input")
        input_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.input_text = scrolledtext.ScrolledText(input_frame, height=10)
        self.input_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        buttons_frame = ttk.Frame(self.translator_frame)
        buttons_frame.pack(padx=10, pady=5, fill=tk.X)

        self.translate_button = ttk.Button(buttons_frame, text="Translate", command=self.translate)
        self.translate_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(buttons_frame, text="Clear", command=self.clear_fields)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="english_to_synapse")
        self.english_to_synapse_radio = ttk.Radiobutton(buttons_frame, text="English to Synapse", variable=self.mode_var, value="english_to_synapse")
        self.english_to_synapse_radio.pack(side=tk.LEFT, padx=5)
        self.synapse_to_english_radio = ttk.Radiobutton(buttons_frame, text="Synapse to English", variable=self.mode_var, value="synapse_to_english")
        self.synapse_to_english_radio.pack(side=tk.LEFT, padx=5)

        output_frame = ttk.LabelFrame(self.translator_frame, text="Output")
        output_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(output_frame, height=10)
        self.output_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

    def setup_explanation_tab(self):
        explanation_text = scrolledtext.ScrolledText(self.explanation_frame, wrap=tk.WORD)
        explanation_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        with open('synapse_explanation.txt', 'r') as f:
            explanation = f.read()
        explanation_text.insert(tk.END, explanation)
        explanation_text.config(state=tk.DISABLED)

    def translate(self):
        input_text = self.input_text.get("1.0", tk.END).strip()
        mode = self.mode_var.get()

        try:
            if mode == "english_to_synapse":
                output = self.english_to_synapse(input_text)
            else:
                output = self.synapse_to_english(input_text)
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, output)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            log_error(f"Translation error: {str(e)}")

    def english_to_synapse(self, text):
        sentences = sent_tokenize(text)
        synapse_sentences = []
        
        for sentence in sentences:
            tokens = self.tokenize(sentence)
            parsed = self.parse(tokens)
            synapse = self.convert_to_synapse(parsed)
            synapse = self.apply_synapse_patterns(synapse)
            synapse_sentences.append(synapse)
        
        return self.combine_synapse_sentences(synapse_sentences)

    def synapse_to_english(self, text):
        # Parse the Synapse text into a structured format
        parsed = self.parse_synapse(text)
        
        # Convert the parsed Synapse to English
        english = self.convert_to_english(parsed)
        
        # Apply English patterns for better readability
        english = self.apply_english_patterns(english)
        
        return english

    def tokenize(self, text):
        return word_tokenize(text)

    def parse(self, tokens):
        tagged = pos_tag(tokens)
        return ne_chunk(tagged)

    def convert_to_synapse(self, parsed):
        def process_subtree(subtree):
            if isinstance(subtree, Tree):
                entity_type = subtree.label()
                entity_value = ' '.join([word for word, tag in subtree.leaves()])
                return f"@{entity_type}({entity_value})"
            else:
                word, tag = subtree
                synapse_quark = synapse_dictionary.get(word.lower(), word)
                return f"@{tag}({synapse_quark})"

        def traverse(tree):
            if isinstance(tree, Tree):
                return ' '.join(traverse(subtree) for subtree in tree)
            else:
                return process_subtree(tree)

        return traverse(parsed)

    def apply_synapse_patterns(self, synapse):
        for pattern in pattern_matching['english_to_synapse']:
            synapse = re.sub(pattern['pattern'], pattern['replacement'], synapse)
        return synapse

    def combine_synapse_sentences(self, sentences):
        combined = "[START]\n"
        for i, sentence in enumerate(sentences):
            if i == 0:
                combined += "[PRED]"
            combined += sentence + "\n"
        combined += "[END]"
        return combined

    def parse_synapse(self, text):
        # Remove [START] and [END] tags
        text = text.replace("[START]", "").replace("[END]", "").strip()
        
        # Split the text into sections based on Synapse markers
        sections = re.split(r'\[(?:PRED|Q|R|HYPO)\]', text)
        sections = [section.strip() for section in sections if section.strip()]
        
        parsed_sections = []
        for section in sections:
            parsed_section = self.parse_synapse_section(section)
            parsed_sections.append(parsed_section)
        
        return parsed_sections

    def parse_synapse_section(self, section):
        tokens = re.findall(r'@\w+(?:\{[^}]+\})?|\([^)]+\)|[^@()]+', section)
        parsed = []
        for token in tokens:
            if token.startswith('@'):
                quark, content = token.split('{', 1) if '{' in token else (token, '')
                content = content.rstrip('}')
                parsed.append((quark, content))
            elif token.startswith('('):
                parsed.append(('EXPR', token.strip('()')))
            else:
                parsed.append(('TEXT', token.strip()))
        return parsed

    def convert_to_english(self, parsed_sections):
        english_sections = []
        for section in parsed_sections:
            english_section = self.convert_section_to_english(section)
            english_sections.append(english_section)
        
        return ' '.join(english_sections)

    def convert_section_to_english(self, section):
        english = []
        for i, (token_type, content) in enumerate(section):
            if token_type == '@P':
                english.append(self.convert_person(content))
            elif token_type == '@A':
                english.append(self.convert_action(content))
            elif token_type == '@R':
                english.append(self.convert_relation(content))
            elif token_type == '@C':
                english.append(self.convert_concept(content))
            elif token_type == '@S':
                english.append(self.convert_state(content))
            elif token_type == 'EXPR':
                english.append(self.convert_expression_to_english(content))
            elif token_type == 'TEXT':
                english.append(content)
        
        return ' '.join(english)

    def convert_person(self, content):
        return content if content else "someone"

    def convert_action(self, content):
        return f"performs {content}" if content else "acts"

    def convert_relation(self, content):
        return content if content else "relates to"

    def convert_concept(self, content):
        return f"the concept of {content}" if content else "a concept"

    def convert_state(self, content):
        return f"the state of {content}" if content else "a state"

    def convert_expression_to_english(self, expr):
        # Convert Synapse expressions to English
        expr = expr.replace('Δ', 'changes in ')
        expr = expr.replace('⊗', 'and ')
        expr = expr.replace('∃', 'there exists ')
        expr = expr.replace('∀', 'for all ')
        expr = expr.replace('¬', 'not ')
        expr = re.sub(r'⟨t\+(\d+)⟩', r'in \1 time units', expr)
        expr = re.sub(r'⟨(\w+)⟩', r'\1', expr)
        return expr

    def apply_english_patterns(self, english):
        for pattern in pattern_matching['synapse_to_english']:
            if re.search(pattern['pattern'], english):
                replacement = pattern['replacement']
                replacement = re.sub(r'\{(\d+)\}', r'\\\1', replacement)
                print(f"Applying pattern: {pattern['pattern']} -> {replacement}")
                english = re.sub(pattern['pattern'], replacement, english)

        english = english.replace('AI', 'artificial intelligence')
        english = english.replace('HUMAN', 'humans')
        english = re.sub(r'\bthe concept of of\b', 'the concept of', english)
        english = re.sub(r'\bstate of\b', '', english)

        # Additional transformations for more natural language
        english = re.sub(r'there exists (\w+) (\w+)', r'there is a \1 that \2s', english)
        english = re.sub(r'for all (\w+)', r'for all \1s', english)
        english = english.replace('changes in advance', 'continues to advance')
        english = english.replace('in n time units', 'in the future')
        english = re.sub(r'in (\d+) time units', r'by \1', english)
        english = english.replace('performs cognition', 'cognitive capabilities')
        english = re.sub(r'changes in (\w+), (\w+), and (\w+)', r'changes in \1, \2, and \3 structures', english)

        # Sentence starters
        english = "As " + english
        english = english.replace(' there is', '. There is')
        english = english.replace(' by 2050', '. By 2050')
        english = english.replace(' this development', '. This development')

        print(f"After applying patterns: {english}")
        return english

    def translate(self):
        input_text = self.input_text.get("1.0", tk.END).strip()
        mode = self.mode_var.get()

        try:
            if mode == "english_to_synapse":
                output = self.english_to_synapse(input_text)
            else:
                output = self.synapse_to_english(input_text)
            
            print(f"Translation result: {output}")
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, output)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            log_error(f"Translation error: {str(e)}")

    def clear_fields(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)

def log_error(error):
    with open('error_log.txt', 'a') as f:
        f.write(f"{error}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = SynapseTranslator(root)
    root.mainloop()