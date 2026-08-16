document.addEventListener('DOMContentLoaded', function () {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const previewBox = document.getElementById('previewBox');
  const previewImg = document.getElementById('previewImg');
  const submitBtn = document.getElementById('submitBtn');
  const form = document.getElementById('uploadForm');
  const laserLine = document.getElementById('laserLine');
  const scannerOverlay = document.getElementById('scannerOverlay');
  const scannerStepText = document.getElementById('scannerStepText');
  const scannerProgressFill = document.getElementById('scannerProgressFill');

  // Drag and drop handlers
  dropzone.addEventListener('dragover', function (e) {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });

  dropzone.addEventListener('dragleave', function () {
    dropzone.classList.remove('drag-over');
  });

  dropzone.addEventListener('drop', function (e) {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  dropzone.addEventListener('click', function (e) {
    if (e.target.tagName !== 'BUTTON') fileInput.click();
  });

  fileInput.addEventListener('change', function () {
    if (this.files[0]) handleFile(this.files[0]);
  });

  function handleFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const allowedExts = ['jpg', 'jpeg', 'png', 'bmp', 'dcm'];
    if (!allowedExts.includes(ext)) {
      alert('Please upload a valid retinal file (JPG, PNG, BMP, or DICOM .dcm).');
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      alert('File size must be under 16 MB.');
      return;
    }

    // Set file to input
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;

    // Show preview or placeholder for DICOM
    if (ext === 'dcm') {
      previewImg.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="%2300f0ff"><rect x="20" y="10" width="60" height="80" rx="5" fill="none" stroke="%2300f0ff" stroke-width="3"/><text x="50" y="45" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="middle" fill="%2300f0ff">DICOM</text><text x="50" y="65" font-family="sans-serif" font-size="8" text-anchor="middle" fill="%239ca3af">MEDICAL IMAGE</text></svg>';
      dropzone.style.display = 'none';
      previewBox.style.display = 'block';
    } else {
      const reader = new FileReader();
      reader.onload = function (e) {
        previewImg.src = e.target.result;
        dropzone.style.display = 'none';
        previewBox.style.display = 'block';
      };
      reader.readAsDataURL(file);
    }
  }

  // Intercept form submission and run high-tech diagnostics animation
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // Disable button to prevent double-clicks
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Diagnostics Running...';

    // Show laser and progress overlay
    laserLine.style.display = 'block';
    scannerOverlay.classList.add('active');

    const steps = [
      { text: "DICOM format checks & metadata verification...", progress: 25, duration: 1000 },
      { text: "Applying CLAHE contrast enhancements & resizing...", progress: 50, duration: 1200 },
      { text: "Executing CNN diabetic retinopathy classification...", progress: 75, duration: 1200 },
      { text: "Extracting Grad-CAM features & generating heatmaps...", progress: 100, duration: 1100 }
    ];

    let currentStep = 0;

    function runDiagnosticStep() {
      if (currentStep < steps.length) {
        const step = steps[currentStep];
        scannerStepText.innerText = step.text;
        scannerProgressFill.style.width = step.progress + "%";
        
        setTimeout(() => {
          currentStep++;
          runDiagnosticStep();
        }, step.duration);
      } else {
        // Complete, submit form
        form.submit();
      }
    }

    runDiagnosticStep();
  });
});

function clearPreview() {
  document.getElementById('previewBox').style.display = 'none';
  document.getElementById('dropzone').style.display = 'block';
  document.getElementById('previewImg').src = '';
  document.getElementById('fileInput').value = '';
  document.getElementById('laserLine').style.display = 'none';
  document.getElementById('scannerOverlay').classList.remove('active');
  
  const submitBtn = document.getElementById('submitBtn');
  submitBtn.disabled = false;
  submitBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Analyse Image';
}

// --- Batch Scan Upload & Processing Logic ---
window.toggleUploadMode = function(mode) {
  const singleMode = document.getElementById('modeSingle');
  const batchMode = document.getElementById('modeBatch');
  const btnSingle = document.getElementById('btnTabSingle');
  const btnBatch = document.getElementById('btnTabBatch');
  
  if (mode === 'single') {
    singleMode.style.display = 'block';
    batchMode.style.display = 'none';
    btnSingle.style.borderBottomColor = 'var(--neon-cyan)';
    btnSingle.style.background = 'rgba(0,240,255,0.03)';
    btnBatch.style.borderBottomColor = 'transparent';
    btnBatch.style.background = 'none';
  } else {
    singleMode.style.display = 'none';
    batchMode.style.display = 'block';
    btnSingle.style.borderBottomColor = 'transparent';
    btnSingle.style.background = 'none';
    btnBatch.style.borderBottomColor = 'var(--neon-purple)';
    btnBatch.style.background = 'rgba(189,0,255,0.03)';
  }
};

window.startBatchProcessing = function() {
  const filesInput = document.getElementById('batchFileInput');
  const files = filesInput.files;
  const eyeSide = document.getElementById('batch_eye_side').value;
  const submitBtn = document.getElementById('batchSubmitBtn');
  
  if (files.length === 0) {
    alert("Please select or drag-and-drop some retinal photos first.");
    return;
  }
  
  if (files.length < 2 || files.length > 50) {
    alert("Batch scan uploads require between 2 and 50 images in queue.");
    return;
  }
  
  // Disable button
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up fa-spin"></i> Uploading Batch Files...';
  
  // Build payload
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('retinal_images', files[i]);
  }
  formData.append('eye_side', eyeSide);
  
  // POST files
  fetch('/upload-batch', {
    method: 'POST',
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (!data.success) {
      alert("Error: " + data.message);
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fa-solid fa-gears"></i> Upload & Process Batch Queue';
      return;
    }
    
    // Initialise UI Queue visualizer
    document.getElementById('batchDropzone').style.display = 'none';
    document.getElementById('batchQueueContainer').style.display = 'block';
    document.getElementById('batchSpinner').style.display = 'inline-block';
    
    const scans = data.scans;
    document.getElementById('queueTotal').innerText = scans.length;
    document.getElementById('queueProcessed').innerText = '0';
    
    const tbody = document.getElementById('batchQueueTableBody');
    tbody.innerHTML = '';
    
    // Inject scan rows
    scans.forEach(s => {
      const tr = document.createElement('tr');
      tr.id = `queue-row-${s.id}`;
      tr.innerHTML = `
        <td style="font-weight:600;">${s.filename}</td>
        <td class="col-quality"><span class="badge badge-pending">Waiting...</span></td>
        <td class="col-ai"><span class="badge badge-pending">Waiting...</span></td>
        <td class="col-status"><i class="fa-solid fa-clock-rotate-left" style="color:var(--text-secondary);"></i> Enqueued</td>
      `;
      tbody.appendChild(tr);
    });
    
    // Process queue sequentially
    processQueueSequentially(scans, 0);
  })
  .catch(err => {
    console.error(err);
    alert("Batch upload connection failed.");
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa-solid fa-gears"></i> Upload & Process Batch Queue';
  });
};

function processQueueSequentially(scans, index) {
  if (index >= scans.length) {
    // Queue complete
    document.getElementById('batchSpinner').style.display = 'none';
    const submitBtn = document.getElementById('batchSubmitBtn');
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-check" style="color:var(--neon-green);"></i> Batch Processing Complete';
    return;
  }
  
  const scan = scans[index];
  const row = document.getElementById(`queue-row-${scan.id}`);
  
  // Set active row state
  row.querySelector('.col-status').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin" style="color:var(--neon-purple);"></i> Processing...';
  
  fetch(`/api/process-scan/${scan.id}`, {
    method: 'POST'
  })
  .then(res => res.json())
  .then(result => {
    // Update queue count & progress bar
    const processed = index + 1;
    document.getElementById('queueProcessed').innerText = processed;
    const progressPerc = (processed / scans.length) * 100;
    document.getElementById('batchProgressBar').style.width = progressPerc + '%';
    
    if (result.success) {
      // Success update
      row.querySelector('.col-quality').innerHTML = `<span style="color:var(--neon-green); font-weight:600;"><i class="fa-solid fa-circle-check"></i> ${result.quality_score}%</span>`;
      row.querySelector('.col-ai').innerHTML = `<span class="badge badge-no-dr">${result.predicted_class} (${result.confidence}%)</span>`;
      row.querySelector('.col-status').innerHTML = `<a href="/results/${result.id}" target="_blank" class="btn btn-outline btn-sm" style="border-color:var(--neon-cyan); color:var(--neon-cyan); padding:0.15rem 0.5rem;"><i class="fa-solid fa-square-poll-vertical"></i> View Results</a>`;
    } else {
      // Error quality validation update
      row.querySelector('.col-quality').innerHTML = `<span style="color:var(--neon-pink); font-weight:600;"><i class="fa-solid fa-circle-xmark"></i> Rejected</span>`;
      row.querySelector('.col-ai').innerHTML = `<span style="color:var(--text-secondary); font-size:0.75rem;">Quality Rejected</span>`;
      row.querySelector('.col-status').innerHTML = `<span class="badge badge-severe-dr" title="${result.issues.join(', ')}"><i class="fa-solid fa-triangle-exclamation"></i> Quality Error</span>`;
    }
    
    // Process next item
    processQueueSequentially(scans, index + 1);
  })
  .catch(err => {
    console.error(err);
    row.querySelector('.col-status').innerHTML = '<span class="badge badge-severe-dr"><i class="fa-solid fa-xmark"></i> Connection Error</span>';
    processQueueSequentially(scans, index + 1);
  });
}
