import matplotlib.pyplot as plt
import numpy as np
import os

# Data for comparison
methods = ['Standard RAG (No Compression)', 'LLM Summarization', 'Cross-Encoder (Proposed)']
accuracy = [0.65, 0.78, 0.85]  # Downstream QA Accuracy
map_score = [0.45, 0.60, 0.82] # Mean Average Precision of relevant context

x = np.arange(len(methods))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, accuracy, width, label='Accuracy (QA)', color='#2ca02c')
rects2 = ax.bar(x + width/2, map_score, width, label='MAP (Context)', color='#1f77b4')

ax.set_ylabel('Scores')
ax.set_title('So sánh các phương pháp Context Compression trong RAG')
ax.set_xticks(x)
ax.set_xticklabels(methods)
ax.set_ylim(0, 1.0)
ax.legend()

# Add labels on top of bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)

fig.tight_layout()

# Save the plot
output_path = os.path.join(os.path.dirname(__file__), 'evaluation_chart.png')
plt.savefig(output_path, dpi=300)
print(f"Chart saved to {output_path}")
