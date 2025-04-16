async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
  
    const formData = new FormData();
    formData.append('file', file);
  
    const response = await fetch('http://localhost:8000/upload', {
      method: 'POST',
      body: formData
    });
  
    const result = await response.json();
    alert(`Tải lên thành công: ${result.filename}`);
  }
  
  async function askQuestion() {
    const question = document.getElementById('questionInput').value;
  
    const response = await fetch(`http://localhost:8000/ask?question=${encodeURIComponent(question)}`);
    const result = await response.json();
  
    document.getElementById('answerText').textContent = result.answer;
  }
  