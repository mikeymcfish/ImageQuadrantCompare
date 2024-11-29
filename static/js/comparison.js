document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.comparison-container');
    const mouseOverlay = document.querySelector('.mouse-overlay');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    const zoomInBtn = document.getElementById('zoomInBtn');
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    const resetZoomBtn = document.getElementById('resetZoomBtn');
    const imageLayers = document.querySelectorAll('.image-layer');
    
    let currentZoom = 1;
    const ZOOM_STEP = 0.1;
    const MAX_ZOOM = 3;
    const MIN_ZOOM = 0.5;
    
    let isDragging = false;
    let startPanX = 0;
    let startPanY = 0;
    let currentPanX = 0;
    let currentPanY = 0;

    function updateClipPaths(e) {
        const rect = container.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        
        // Clamp values between 0 and 100
        const clampedX = Math.min(100, Math.max(0, x));
        const clampedY = Math.min(100, Math.max(0, y));
        
        // Update CSS variables for clip paths
        container.style.setProperty('--clip-x', `${clampedX}%`);
        container.style.setProperty('--clip-y', `${clampedY}%`);
    }

    // Mouse movement handler
    mouseOverlay.addEventListener('mousemove', updateClipPaths);

    // Touch support
    // Zoom controls
    function updateZoom() {
        imageLayers.forEach(layer => {
            layer.style.transform = `scale(${currentZoom}) translate(${currentPanX}px, ${currentPanY}px)`;
        });
    }

    zoomInBtn.addEventListener('click', () => {
        if (currentZoom < MAX_ZOOM) {
            currentZoom = Math.min(currentZoom + ZOOM_STEP, MAX_ZOOM);
            updateZoom();
        }
    });

    zoomOutBtn.addEventListener('click', () => {
        if (currentZoom > MIN_ZOOM) {
            currentZoom = Math.max(currentZoom - ZOOM_STEP, MIN_ZOOM);
            updateZoom();
        }
    });

    resetZoomBtn.addEventListener('click', () => {
        currentZoom = 1;
        currentPanX = 0;
        currentPanY = 0;
        updateZoom();
    });

    // Pan functionality
    mouseOverlay.addEventListener('mousedown', (e) => {
        if (e.buttons === 2) { // Right mouse button
            isDragging = true;
            startPanX = e.clientX - currentPanX;
            startPanY = e.clientY - currentPanY;
            mouseOverlay.style.cursor = 'grabbing';
        }
    });

    mouseOverlay.addEventListener('mousemove', (e) => {
        if (isDragging && e.buttons === 2) {
            currentPanX = e.clientX - startPanX;
            currentPanY = e.clientY - startPanY;
            updateZoom();
        } else {
            updateClipPaths(e);
        }
    });

    mouseOverlay.addEventListener('mouseup', () => {
        isDragging = false;
        mouseOverlay.style.cursor = 'move';
    });

    mouseOverlay.addEventListener('mouseleave', () => {
        isDragging = false;
        mouseOverlay.style.cursor = 'move';
    });

    // Prevent context menu on right-click
    mouseOverlay.addEventListener('contextmenu', (e) => {
        e.preventDefault();
    });

    mouseOverlay.addEventListener('touchmove', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        updateClipPaths(touch);
    });

    // Fullscreen support
    fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            container.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    });

    // Set initial clip paths to center
    container.style.setProperty('--clip-x', '50%');
    container.style.setProperty('--clip-y', '50%');

    // Track pressed keys
    const pressedKeys = new Set();

    // Reset all images to default state
    function resetImages() {
        imageLayers.forEach(layer => {
            layer.style.opacity = '1';
            layer.style.clipPath = '';
        });
        container.style.setProperty('--clip-x', '50%');
        container.style.setProperty('--clip-y', '50%');
    }

    // Update images based on currently pressed keys
    function updateImages() {
        // Reset all images first
        imageLayers.forEach(layer => {
            layer.style.opacity = '0';
            layer.style.clipPath = 'none';
        });

        const activeImages = [];

        // Map keys to image indices (0: top-left, 1: top-right, 2: bottom-left, 3: bottom-right)
        if (pressedKeys.has('ArrowUp')) activeImages.push(0);     // Top-left
        if (pressedKeys.has('ArrowRight')) activeImages.push(1);  // Top-right
        if (pressedKeys.has('ArrowLeft')) activeImages.push(2);   // Bottom-left
        if (pressedKeys.has('ArrowDown')) activeImages.push(3);   // Bottom-right

        // If no keys are pressed, reset to default state
        if (activeImages.length === 0) {
            resetImages();
            return;
        }

        // Show active images with proper opacity
        const opacity = 1 / activeImages.length;
        activeImages.forEach(index => {
            imageLayers[index].style.opacity = opacity.toString();
            imageLayers[index].style.clipPath = 'none';
        });
    }

    // Keyboard controls
    document.addEventListener('keydown', (e) => {
        if (['ArrowUp', 'ArrowRight', 'ArrowDown', 'ArrowLeft'].includes(e.key)) {
            e.preventDefault();
            pressedKeys.add(e.key);
            updateImages();
        }
    });

    document.addEventListener('keyup', (e) => {
        if (['ArrowUp', 'ArrowRight', 'ArrowDown', 'ArrowLeft'].includes(e.key)) {
            e.preventDefault();
            pressedKeys.delete(e.key);
            updateImages();
        }
    });

    // Reset when window loses focus
    window.addEventListener('blur', () => {
        pressedKeys.clear();
        resetImages();
    });
});
