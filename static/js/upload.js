document.addEventListener('DOMContentLoaded', function() {
    const dragArea = document.getElementById('dragArea');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dragArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dragArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dragArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dragArea.addEventListener('drop', handleDrop, false);

    // Handle click to select files
    dragArea.addEventListener('click', () => {
        fileInput.click();
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dragArea.classList.add('dragover');
    }

    function unhighlight(e) {
        dragArea.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        // Update the file input with the dropped files
        fileInput.files = files;
        
        // If files are dropped, submit the form automatically
        if (files.length > 0) {
            uploadForm.submit();
        }
    }
});
