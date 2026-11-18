import pandas as pd
import matplotlib.pyplot as plt
from search_engine import HybridSearcher

def run_benchmark(csv_db_path, queries_path):
    engine = HybridSearcher(csv_db_path)
    test_cases = pd.read_csv(queries_path)
    
    results = {"BM25-Only": {"Top-1": 0, "Top-3": 0, "MRR": 0.0},
               "Hybrid": {"Top-1": 0, "Top-3": 0, "MRR": 0.0}}
    
    n = len(test_cases)
    
    for _, row in test_cases.iterrows():
        q = row['Query']
        expected = row['Expected_ID']
        
        # Test Hybrid
        hybrid_res = engine.search(q, top_k=3)['ID'].tolist()
        if expected in hybrid_res:
            results["Hybrid"]["Top-3"] += 1
            if expected == hybrid_res[0]:
                results["Hybrid"]["Top-1"] += 1
            results["Hybrid"]["MRR"] += 1.0 / (hybrid_res.index(expected) + 1)
            
    # Calculate averages
    for model in results:
        results[model]["Top-1"] = (results[model]["Top-1"] / n) * 100
        results[model]["Top-3"] = (results[model]["Top-3"] / n) * 100
        results[model]["MRR"] = results[model]["MRR"] / n

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    metrics = ['Top-1 (%)', 'Top-3 (%)', 'MRR (score)']
    hybrid_vals = [results["Hybrid"]["Top-1"], results["Hybrid"]["Top-3"], results["Hybrid"]["MRR"]]
    
    x = range(len(metrics))
    ax.bar(x, hybrid_vals, width=0.4, label='Hybrid Ranker', color='#3B82F6')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_title("Search Architecture Benchmark")
    plt.legend()
    plt.savefig('benchmark_results.png')
    
    # Save README table string
    table = f"| Metric | Hybrid |\n|---|---|\n| Top-1 | {results['Hybrid']['Top-1']:.1f}% |\n| Top-3 | {results['Hybrid']['Top-3']:.1f}% |\n| MRR | {results['Hybrid']['MRR']:.3f} |"
    with open('benchmark_readme_table.txt', 'w') as f:
        f.write(table)
    
    print("Benchmark completed. Visuals saved.")

if __name__ == "__main__":
    run_benchmark('EAFC_27_Complete_Controls_2.csv', 'queries.csv')