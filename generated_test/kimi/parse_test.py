import re

input_file = '/Users/jb/Downloads/DSAT_GRAMMAR_GT/generated_test/kimi/generated_dsat_pt11_m2_highcomp_v1.md'
output_file = '/Users/jb/Downloads/DSAT_GRAMMAR_GT/generated_test/kimi/student_dsat_pt11_m2_highcomp_v1.md'

with open(input_file, 'r') as f:
    lines = f.readlines()

out_lines = []
skip_mode = False

for line in lines:
    # Skip answer key and everything after
    if line.startswith('## Answer Key'):
        break
        
    # Skip Correct Answer and Explanation
    if line.startswith('**Correct Answer:'):
        continue
    if line.startswith('**Explanation:'):
        continue
        
    # Skip generation metadata at the top
    if line.startswith('**Source Pattern:**') or line.startswith('**Difficulty Level:**') or line.startswith('**Generation Model:**'):
        continue
        
    # Clean up Block headers but keep Directions
    if line.startswith('## Block'):
        continue
        
    out_lines.append(line)

# Clean up multiple consecutive blank lines
text = "".join(out_lines)
text = re.sub(r'\n{3,}', '\n\n', text)

with open(output_file, 'w') as f:
    f.write(text.strip() + "\n")

print("Created student version at:", output_file)
