<script>
  import { onMount } from 'svelte';
  import Results from './lib/Results.svelte';
  import Sidebar from './lib/Sidebar.svelte';

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const RESULTS_ENDPOINT = `${API_URL}/evaluation-results`;

  let query = '';
  let isLoading = false;
  let loadingStatus = { current: 0, total: 5, message: '' };
  let currentImages = {};
  let currentSelections = {};
  let results = { queries: [], results: {} };
  let methodAccuracy = {};
  let sidebarCollapsed = false;

  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
  }

  // Initialize method accuracy tracking
  onMount(async () => {
    initMethodAccuracy();
    await loadResults();
  });

  function initMethodAccuracy() {
    // Initialize method accuracy tracking for all structures
    methodAccuracy = {};
    
    ["bge", "tfidf", "bm25_with_stopwords", "bm25_without_stopwords"].forEach(method => {
      for (let structure = 1; structure <= 5; structure++) {
        methodAccuracy[`${method}_structure${structure}`] = { correct: 0, total: 0 };
      }
    });
    
    methodAccuracy["clip"] = { correct: 0, total: 0 };
  }

  async function fetchImages() {
    if (!query.trim()) return;
    
    isLoading = true;
    loadingStatus = { current: 0, total: 5, message: 'Starting retrieval...' };
    
    try {
      const response = await fetch(`${API_URL}/get-images?query=${encodeURIComponent(query)}&k=1`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch images');
      }
      
      const data = await response.json();
      currentImages = data.results;
      
      // Initialize selections to "Incorrect" for all new images
      initializeSelections(currentImages);
      
      loadingStatus = { current: 5, total: 5, message: 'Completed!' };
    } catch (error) {
      console.error('Error fetching images:', error);
      alert('Failed to fetch images. Please try again.');
    } finally {
      isLoading = false;
    }
  }
  
  // Helper function to initialize all selections to "Incorrect"
  function initializeSelections(images) {
    currentSelections = {};
    
    // Initialize for structured retrievers (BGE, TF-IDF, BM25)
    ["bge", "tfidf", "bm25_with_stopwords", "bm25_without_stopwords"].forEach(method => {
      if (images[method]) {
        Object.entries(images[method]).forEach(([structureNum, structureImages]) => {
          if (structureImages && structureImages.length > 0) {
            const imageId = `${method}_structure${structureNum}_0`;
            currentSelections[imageId] = "Incorrect";
          }
        });
      }
    });
    
    // Initialize for CLIP
    if (images.clip && images.clip.length > 0) {
      currentSelections["clip_0"] = "Incorrect";
    }
  }

  async function loadResults() {
    try {
      const response = await fetch(`${RESULTS_ENDPOINT}`);
      
      if (response.ok) {
        const data = await response.json();
        results = data;
        
        // Recalculate method accuracies from saved results
        if (results.results) {
          Object.values(results.results).forEach(queryResult => {
            if (queryResult.selections) {
              Object.entries(queryResult.selections).forEach(([imageId, selection]) => {
                // console.log(imageId, selection);
                updateMethodAccuracy(imageId, selection);
              });
            }
          });
        }
      } else {
        console.warn('No existing results found, starting with empty results.');
        results = { queries: [], results: {} };
      }
    } catch (error) {
      console.error('Error loading results:', error);
      alert('Failed to load previous evaluation results. Starting fresh.');
      results = { queries: [], results: {} };
    }
  }

  async function saveResults() {
    try {
      const response = await fetch(`${RESULTS_ENDPOINT}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(results)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save results');
      }
    } catch (error) {
      console.error('Error saving results:', error);
      alert('Failed to save evaluation results. Please try again.');
    }
  }

  function updateMethodAccuracy(imageId, selection) {
    let methodKey = null;
    const parts = imageId.split('_');
    
    if (imageId.includes('structure') && parts.length >= 3) {
      let method;
      let structure;

      if(parts[0] == "bm25"){
        method = parts[0] + "_" + parts[1] + "_" + parts[2];
        structure = parts[3];
      } else {
        method = parts[0];
        structure = parts[1];
      }

      methodKey = `${method}_${structure}`;
    } else {
      methodKey = parts[0];
    }
    
    if (methodAccuracy[methodKey]) {
      methodAccuracy[methodKey].total += 1;
      if (selection === 'Correct') {
        methodAccuracy[methodKey].correct += 1;
      }
    }
  }

  async function handleSubmitEvaluation() {
    // Update method accuracies
    Object.entries(currentSelections).forEach(([imageId, selection]) => {
      updateMethodAccuracy(imageId, selection);
    });
    
    // Save results
    const queryResults = {
      query,
      timestamp: new Date().toISOString(),
      selections: currentSelections,
      images: currentImages
    };
    
    if (!results.queries.includes(query)) {
      results.queries.push(query);
    }
    
    results.results[query] = queryResults;
    await saveResults();
    
    // Reset state
    currentSelections = {};
    currentImages = {};
    query = '';
    
    // alert('Evaluation submitted successfully!');
  }

  function handleSelectionChange(event) {
    const { imageId, value } = event.detail;
    currentSelections[imageId] = value;
  }
</script>

<main class={sidebarCollapsed ? 'sidebar-collapsed' : ''}>
  <div class="content-area">
    <header>
      <h1>
        Image Retrieval Evaluation
        <button class="toggle-sidebar" on:click={toggleSidebar}>
          {sidebarCollapsed ? '»' : '«'}
        </button>
      </h1>
    </header>
    
    <div>
      <form on:submit|preventDefault={fetchImages}>
        <input 
          type="text" 
          bind:value={query} 
          placeholder="Enter your search query..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !query.trim()}>
          {isLoading ? 'Retrieving...' : 'Retrieve Images'}
        </button>
      </form>
      
      {#if isLoading}
        <div class="loading">
          <progress value={loadingStatus.current} max={loadingStatus.total}></progress>
          <p>{loadingStatus.message}</p>
        </div>
      {/if}
    </div>
    
    {#if Object.keys(currentImages).length > 0}
      <Results 
        images={currentImages} 
        selections={currentSelections}
        on:selectionChange={handleSelectionChange}
        on:submit={handleSubmitEvaluation}
      />
    {/if}
  </div>
  
  {#if !sidebarCollapsed}
    <Sidebar 
      results={results} 
      methodAccuracy={methodAccuracy}
    />
  {/if}
</main>

<style>
  main {
    display: flex;
    width: 100%;
    max-width: 100%;
    gap: 1rem;
    position: relative;
  }
  
  .content-area {
    flex: 1;
    min-width: 0;
    padding: 0 1rem;
    transition: width 0.3s ease;
  }
  
  /* When sidebar is collapsed, make content area take full width */
  .sidebar-collapsed {
    width: 100%;
  }
  
  .sidebar-collapsed .content-area {
    width: 100%;
    max-width: 100%;
  }
  
  header {
    margin-bottom: 2rem;
  }
  
  h1 {
    color: #333;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
  
  form {
    display: flex;
    gap: 1rem;
  }
  
  input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  button {
    padding: 0.75rem 1.5rem;
    background-color: #4361ee;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
  }
  
  button:hover {
    background-color: #3a56d4;
  }
  
  button:disabled {
    background-color: #a0a0a0;
    cursor: not-allowed;
  }
  
  .loading {
    margin-top: 1rem;
  }
  
  progress {
    width: 100%;
    height: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .toggle-sidebar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background-color: #4361ee;
    color: white;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: none;
    z-index: 10;
    font-size: 18px;
    padding: 0;
    margin-left: 10px;
  }
</style>

