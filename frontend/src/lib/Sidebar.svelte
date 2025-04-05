<script>
  export let results = { queries: [], results: {} };
  export let methodAccuracy = {};
  
  // Format method names for display
  const methodLabels = {
    "bge": "BGE",
    "tfidf": "TF-IDF",
    "bm25_with_stopwords": "BM25+SW",
    "bm25_without_stopwords": "BM25-SW",
    "clip": "CLIP"
  };
  
  // Function to get all retriever stats in flat format
  function getRetrieverStats() {
    const stats = [];
    // console.log(results);
    // Add CLIP (separate retriever)
    if (methodAccuracy["clip"]) {
      const clipStats = methodAccuracy["clip"];
      const accuracy = clipStats.total > 0 ? (clipStats.correct / clipStats.total) * 100 : 0;
      stats.push({
        method: "CLIP",
        correct: clipStats.correct,
        total: clipStats.total,
        accuracy: accuracy
      });
    }
    
    // Add all structure-specific retrievers (20 total - 4 methods × 5 structures)
    ["bge", "tfidf", "bm25_with_stopwords", "bm25_without_stopwords"].forEach(method => {
      for (let structure = 1; structure <= 5; structure++) {
        const key = `${method}_structure${structure}`;
        if (methodAccuracy[key]) {
          // console.log(key, methodAccuracy[key]);
          const retrieverStats = methodAccuracy[key];
          const accuracy = retrieverStats.total > 0 ? (retrieverStats.correct / retrieverStats.total) * 100 : 0;
          stats.push({
            method: `${methodLabels[method]} ${structure}`,
            correct: retrieverStats.correct,
            total: retrieverStats.total,
            accuracy: accuracy
          });
        }
      }
    });

    // console.log(stats);
    
    return stats;
  }
</script>

<aside class="sidebar">
  <div class="sidebar-content">
    <h2>Evaluation Statistics</h2>
    <p><strong>Total queries evaluated:</strong> {results.queries.length}</p>
    
    {#if Object.values(methodAccuracy).some(stats => stats.total > 0)}
      <hr/>
      <h2>Retriever Accuracy</h2>
      
      <table>
        <thead>
          <tr>
            <th>Retriever</th>
            <th>Correct/Total</th>
            <th>Accuracy (%)</th>
          </tr>
        </thead>
        <tbody>
          {#each getRetrieverStats() as stat}
            <tr>
              <td>{stat.method}</td>
              <td>{stat.correct}/{stat.total}</td>
              <td>{stat.accuracy.toFixed(2)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</aside>

<style>
  .sidebar {
    position: fixed;
    top: 0;
    right: 0;
    width: 300px;
    height: 100vh;
    background-color: #f5f7fa;
    border-left: 1px solid #e8e8e8;
    overflow-y: auto;
    box-shadow: -2px 0 5px rgba(0, 0, 0, 0.05);
    z-index: 100;
  }
  
  .sidebar-content {
    padding: 1.5rem;
  }
  
  h2 {
    margin-top: 0;
    font-size: 1.5rem;
    color: #333;
    margin-bottom: 1rem;
  }
  
  hr {
    border: 0;
    height: 1px;
    background-color: #e0e0e0;
    margin: 1.5rem 0;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin-top: 1rem;
  }
  
  th, td {
    padding: 0.5rem;
    text-align: left;
    border-bottom: 1px solid #eee;
  }
  
  th {
    font-weight: bold;
    color: #333;
    background-color: #f1f1f1;
  }
</style> 