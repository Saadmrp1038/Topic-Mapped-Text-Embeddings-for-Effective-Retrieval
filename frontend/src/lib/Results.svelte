<script>
  import { createEventDispatcher } from 'svelte';
  
  export let images = {};
  export let selections = {};
  
  const dispatch = createEventDispatcher();
  
  // List of methods and their display names
  const methods = [
    { key: "bge", label: "BGE" },
    { key: "tfidf", label: "TF-IDF" },
    { key: "bm25_with_stopwords", label: "BM25+SW" },
    { key: "bm25_without_stopwords", label: "BM25-SW" },
    { key: "clip", label: "CLIP" }
  ];
  
  function handleSelectionChange(imageId, value) {
    dispatch('selectionChange', { imageId, value });
  }
  
  function handleSubmit() {
    dispatch('submit');
  }
  
  function getImageUrl(imageMetadata) {
    return imageMetadata.image_url;
  }
  
  // Initialize all selections to "Incorrect" by default
  function getDefaultValue(imageId) {
    return selections[imageId] || "Incorrect";
  }
</script>

<section class="results">
  <h2>Retrieved Images</h2>
  
  <div class="image-grid">
    <!-- For structured retrievers (BGE, TF-IDF, BM25) -->
    {#each methods.filter(m => m.key !== "clip") as method}
      {#if images[method.key]}
        {#each Object.entries(images[method.key]) as [structureNum, structureImages]}
          {#if structureImages && structureImages.length > 0}
            <div class="image-card">
              <h3>{method.label} {structureNum}</h3>
              
              {#if 'image_url' in structureImages[0]}
                {@const imageMetadata = structureImages[0]}
                {@const imageId = `${method.key}_structure${structureNum}_0`}
                {@const currentValue = getDefaultValue(imageId)}
                
                <div class="image-container" class:correct={currentValue === "Correct"} class:incorrect={currentValue === "Incorrect"}>
                  <img src={getImageUrl(imageMetadata)} alt="Retrieved image" loading="lazy" />
                </div>
                
                {#if imageMetadata.title}
                  <p class="image-title">{imageMetadata.title.length > 50 ? imageMetadata.title.substring(0, 50) + '...' : imageMetadata.title}</p>
                {/if}
                
                <p class="structure-label">Structure: {structureNum}</p>
                
                <div class="radio-group">
                  <label>
                    <input 
                      type="radio" 
                      name={imageId} 
                      value="Correct" 
                      checked={currentValue === "Correct"} 
                      on:change={() => handleSelectionChange(imageId, "Correct")}
                    />
                    <span>Correct</span>
                  </label>
                  <label>
                    <input 
                      type="radio" 
                      name={imageId} 
                      value="Incorrect" 
                      checked={currentValue === "Incorrect"} 
                      on:change={() => handleSelectionChange(imageId, "Incorrect")}
                    />
                    <span>Incorrect</span>
                  </label>
                </div>
              {/if}
            </div>
          {/if}
        {/each}
      {/if}
    {/each}
    
    <!-- For CLIP -->
    {#if images.clip && images.clip.length > 0}
      <div class="image-card">
        <h3>CLIP</h3>
        
        {#if 'image_url' in images.clip[0]}
          {@const imageMetadata = images.clip[0]}
          {@const imageId = "clip_0"}
          {@const currentValue = getDefaultValue(imageId)}
          
          <div class="image-container" class:correct={currentValue === "Correct"} class:incorrect={currentValue === "Incorrect"}>
            <img src={getImageUrl(imageMetadata)} alt="Retrieved image" loading="lazy" />
          </div>
          
          {#if imageMetadata.title}
            <p class="image-title">{imageMetadata.title.length > 50 ? imageMetadata.title.substring(0, 50) + '...' : imageMetadata.title}</p>
          {/if}
          
          <div class="radio-group">
            <label>
              <input 
                type="radio" 
                name={imageId} 
                value="Correct" 
                checked={currentValue === "Correct"} 
                on:change={() => handleSelectionChange(imageId, "Correct")}
              />
              <span>Correct</span>
            </label>
            <label>
              <input 
                type="radio" 
                name={imageId} 
                value="Incorrect" 
                checked={currentValue === "Incorrect"} 
                on:change={() => handleSelectionChange(imageId, "Incorrect")}
              />
              <span>Incorrect</span>
            </label>
          </div>
        {/if}
      </div>
    {/if}
  </div>
  
  <button class="submit-button" on:click={handleSubmit}>Submit Evaluation</button>
</section>

<style>
  .results {
    margin-top: 2rem;
  }
  
  h2 {
    margin-bottom: 1.5rem;
    text-align: center;
  }
  
  .image-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr); /* Exactly 5 images per row */
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .image-card {
    display: flex;
    flex-direction: column;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    background-color: white;
  }
  
  h3 {
    padding: 0.75rem;
    margin: 0;
    font-size: 0.9rem;
    background-color: #f5f5f5;
    border-bottom: 1px solid #eee;
  }
  
  .image-container {
    position: relative;
    width: 100%;
    height: 180px; 
    overflow: hidden;
    border: 3px solid transparent;
    box-sizing: border-box;
  }
  
  .image-container.correct {
    border-color: #21c45d;
    background-color: rgba(33, 196, 93, 0.1);
  }
  
  .image-container.incorrect {
    border-color: #ff4b4b;
    background-color: rgba(255, 75, 75, 0.1);
  }
  
  img {
    width: 100%;
    height: 100%;
    object-fit: contain; /* This ensures the full image is shown without cropping */
    object-position: center;
  }
  
  .image-title {
    padding: 0.5rem 0.75rem;
    margin: 0;
    font-size: 0.8rem;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .structure-label {
    padding: 0 0.75rem 0.5rem;
    margin: 0;
    font-size: 0.75rem;
    color: #666;
  }
  
  .radio-group {
    display: flex;
    padding: 0.75rem;
    gap: 0.5rem;
    border-top: 1px solid #eee;
    background-color: #f9f9f9;
  }
  
  label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    cursor: pointer;
  }
  
  input[type="radio"] {
    margin: 0;
  }
  
  .submit-button {
    display: block;
    margin: 2rem auto;
    padding: 0.75rem 1.5rem;
    background-color: #4361ee;
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .submit-button:hover {
    background-color: #3a56d4;
  }
</style> 