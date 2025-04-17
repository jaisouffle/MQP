import json
import pandas as pd
import re

data = []

with open("batch_output.jsonl", "r") as f:
    for i, line in enumerate(f, start=1):
        obj = json.loads(line)
        
        custom_id = obj.get("custom_id", "")
        if "|" in custom_id:
            complex_name, technique = custom_id.split("|", 1)
        else:
            complex_name, technique = custom_id, "unknown"

        llm_name = "ChatGPT"  # just for now since only testing with chatGPT

        # try to get the content
        try:
            content = obj["response"]["body"]["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[{i}] Error extracting content for {custom_id}: {e}")
            content = ""

        # clean the string
        content = content.strip().replace("’", "'")
        content = re.sub(r"^'+", "", content)  # remove starting quotes
        content = re.sub(r"\n'+", "\n", content)

        # try regex parse
        match = re.search(
            r"Complex Function:\s*(.*?)\s*Organism:\s*(.*?)\s*Proteins:\s*(.*)",
            content,
            re.DOTALL
        )

        if match:
            complex_function, organism, proteins = match.groups()
            data.append([
                complex_name.strip(),
                technique.strip(),
                llm_name,
                complex_function.strip(),
                organism.strip(),
                proteins.strip()
            ])
        else:
            print(f"[{i}] ⚠️ No match for {custom_id}. Raw content:\n{content[:300]}\n---")
            data.append([
                complex_name.strip(),
                technique.strip(),
                llm_name,
                "PARSE ERROR",
                "UNKNOWN",
                content.strip()
            ])

# create & save the dataframe
df = pd.DataFrame(data, columns=["Complex", "Technique", "LLM", "Complex Function", "Organism", "Proteins"])

if df.empty:
    print("Still no results parsed. Double check your batch_output.jsonl format.")
else:
    df.to_csv("protein_complexes_results_from_batch.csv", index=False)
    print("Results saved to protein_complexes_results_from_batch.csv")
    "contextuall": (
        "You are an expert in the field of biology and molecular machines. Perform a thorough analysis of the protein "
        "complex: {complex}. Avoid overgeneralization and unnecessarily long answers. In your analysis, only include "
        "information that is specific to the organism that the {complex} is most prominent in (either Human, Mouse, "
        "Caenorhabditis elegans, Drosophila melanogaster, or Saccharomyces cerevisiae). Your analysis should include "
        "the organism the complex belongs to, complex name, complex function, list of proteins the complex consists of, "
        "and a list of corresponding genes the proteins belong to. Additionally, list the other organisms that the "
        "protein complex may be found in if applicable. After completing your analysis, also assign a self confidence "
        "score for the data findings to help gauge the accuracy of the information. The score should range from 0.00 to "
        "1.00, with 0.00 being the lowest confidence and 1.00 indicating the highest confidence. To determine your score, "
        "consider the following grading conventions: \n 1. consistency of information across different databases/sources"
        "weight), supporting experimental data regarding the complex(0.3 weight), accuracy of corresponding protein-gene "
        "mapping(0.25 weight), and the analysis information being specific to the organism that it is most promininent "
        "in(0.15 weight). The weight in parentheses following each grading convention signifies how much each criteria "
        "should effect the confidence score with a total of 1.00 if every criteria is completely accurate. Here is an "
        "example of the output for two complexes:\n\n    'Complex Name: ATP4A-ATP4B complex'\n    'Complex Function: "
        "This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible \n    for gastric acid secretion in the stomach.' \n    'Organism: Human'\n    'Other Organisms: N/A'\n    'Proteins: Potassium-transporting ATPase alpha chain 1, Potassium-transporting ATPase subunit beta' \n    'Genes: ATP4A, ATP4B' \n    'Self Confidence Score: 0.97'\n\n    'Complex Name: Sodium leak channel complex'\n    'Complex Function: Voltage-gated ion channel responsible for the depolarizing sodium (Na+) leak currents that determine resting Na(+) permeability and control neuronal excitability. Functions downstream of the molecular circadian clock in pacemaker neurons to promote behavioral rhythmicity.' \n    'Organism: Drosophila melanogaster'\n    'Other Organisms: Human, Caenorhabditis elegans'\n    'Proteins: Protein unc-80 homolog, Narrow abdomen isoform F, Uncoordinated 79 isoform B' \n    'Genes: unc80, na, unc79' \n    'Self Confidence Score: 0.92'         \n    ",        
    ),