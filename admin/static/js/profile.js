// Profile image upload function
async function uploadProfileImage(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file');
        return;
    }
    
    // Check for HEIC/HEIF format
    const fileName = file.name.toLowerCase();
    if (fileName.endsWith('.heic') || fileName.endsWith('.heif') || file.type.toLowerCase().includes('heic')) {
        showErrorNotification('HEIC/HEIF image format is not supported. Please convert to JPEG, PNG, or another standard format.');
        // Clear the file input to prevent upload attempt
        event.target.value = '';
        return;
    }
    
    try {
        // Show loading state
        const imageWrapper = event.target.closest('.profile-image-wrapper');
        let existingImage = imageWrapper.querySelector('.profile-image');
        const placeholderText = imageWrapper.querySelector('.profile-image-placeholder');
        
        // If there's a placeholder text, hide it
        if (placeholderText) {
            placeholderText.style.display = 'none';
        }
        
        // If there's an existing image, update its opacity
        if (existingImage) {
            existingImage.style.opacity = '0.5';
        }

        // Convert image to webp using canvas
        const img = new Image();
        const reader = new FileReader();
        
        reader.onload = async function(e) {
            img.src = e.target.result;
            await new Promise((resolve) => {
                img.onload = resolve;
            });

            // Create canvas and convert to webp
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Calculate new dimensions (max 800x800)
            let width = img.width;
            let height = img.height;
            if (width > 800 || height > 800) {
                const ratio = Math.min(800 / width, 800 / height);
                width *= ratio;
                height *= ratio;
            }
            
            canvas.width = width;
            canvas.height = height;
            ctx.drawImage(img, 0, 0, width, height);
            
            // Convert to webp blob
            canvas.toBlob(async (blob) => {
                const webpFile = new File([blob], 'profile.webp', { type: 'image/webp' });
                
                const formData = new FormData();
                formData.append('file', webpFile);
                
                const response = await fetch('/profile/upload-image', {
                    method: 'POST',
                    body: formData
                });
                
                // Clone the response to read it multiple times if needed
                const responseClone = response.clone();
                
                let result;
                try {
                    result = await response.json();
                } catch (e) {
                    // If JSON parsing fails, try to get the text from the clone
                    const text = await responseClone.text();
                    throw new Error(text || 'Failed to upload image');
                }
                
                if (!response.ok) {
                    throw new Error(result.detail || 'Failed to upload image');
                }
                
                if (result.status === 'success') {
                    // If there's no existing image, create one
                    if (!existingImage) {
                        existingImage = document.createElement('img');
                        existingImage.className = 'profile-image';
                        existingImage.alt = 'Profile Image';
                        imageWrapper.insertBefore(existingImage, imageWrapper.firstChild);
                    }
                    
                    // Update image in UI
                    existingImage.src = `/data/images/profile.webp?t=${Date.now()}`; // Add timestamp to prevent caching
                    existingImage.style.opacity = '1';
                } else {
                    throw new Error(result.detail || 'Failed to upload image');
                }
            }, 'image/webp', 0.85);
        };
        
        reader.readAsDataURL(file);
    } catch (error) {
        console.error('Error uploading image:', error);
        showErrorNotification(error.message || 'Error uploading image. Please try again.');
        
        // Restore original state on error
        const imageWrapper = event.target.closest('.profile-image-wrapper');
        const existingImage = imageWrapper.querySelector('.profile-image');
        const placeholderText = imageWrapper.querySelector('.profile-image-placeholder');
        
        if (existingImage) {
            existingImage.style.opacity = '1';
        }
        if (placeholderText) {
            placeholderText.style.display = 'block';
        }
    }
}

// Notification functions
function showSaveNotification() {
    const notification = document.createElement('div');
    notification.className = 'save-notification';
    notification.innerHTML = `
        <i class="fas fa-check-circle"></i>
        Profile updated successfully!
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        ${message}
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Save all changes function
async function saveAllChanges() {
    try {
        const updates = {
            main_info: {
                name: document.getElementById('name').value,
                job_title: document.getElementById('job_title').value
            },
            contact_card: {
                social_links: {
                    github: {
                        enabled: document.getElementById('github_enabled').checked,
                        url: document.getElementById('github').value
                    },
                    linkedin: {
                        enabled: document.getElementById('linkedin_enabled').checked,
                        url: document.getElementById('linkedin').value
                    }
                }
            },
            about_me: {
                short_description: document.getElementById('short_description').value,
                long_description: document.getElementById('long_description').value
            },
            what_im_doing: {},
            skills: {
                sections: {}
            }
        };

        // Add panels in their current order
        const panels = [...document.querySelectorAll('.what-im-doing-panel')];
        panels.forEach((panel, index) => {
            const panelNum = index + 1;
            const labelText = document.getElementById(`panel${panelNum}_label`).value;
            const imageContent = document.getElementById(`panel${panelNum}_image`).value;
            
            updates.what_im_doing[`panel_${panelNum}`] = {
                enabled: document.getElementById(`panel${panelNum}_enabled`).checked,
                title: document.getElementById(`panel${panelNum}_title`).value,
                description: document.getElementById(`panel${panelNum}_description`).value,
                image: updateSvgColor(imageContent),
                flag: {
                    enabled: labelText !== "",
                    text: labelText
                }
            };
        });

        // Validate and add skills sections
        const sections = [...document.querySelectorAll('.skills-section')];
        sections.forEach(section => {
            const sectionId = section.getAttribute('data-section-id');
            const sectionTitle = section.querySelector('.section-title').value;
            
            updates.skills.sections[sectionId] = {
                title: sectionTitle,
                skills: []
            };
            
            const skills = section.querySelectorAll('.skill-card:not(.add-skill-card)');
            skills.forEach(skill => {
                const skillTitle = skill.getAttribute('data-skill-title');
                const titleInput = skill.querySelector('.skill-title');
                const image = skill.querySelector('.skill-image');
                const backgroundColor = skill.querySelector('.color-picker[onchange*="background"]').value;
                const borderColor = skill.querySelector('.color-picker[onchange*="border"]').value;
                const isNew = skill.querySelector('.flag-toggle input').checked;
                
                updates.skills.sections[sectionId].skills.push({
                    title: titleInput.value,
                    image: image ? image.src.split('/').pop() : '',
                    background_color: backgroundColor,
                    border_color: borderColor,
                    is_new: isNew
                });
            });
        });

        const response = await fetch('/profile/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });

        if (!response.ok) {
            throw new Error('Failed to save changes');
        }

        const result = await response.json();
        if (result.status === 'success') {
            showSaveNotification();
        } else {
            throw new Error(result.detail || 'Failed to save changes');
        }
    } catch (error) {
        console.error('Error saving changes:', error);
        showErrorNotification(error.message || 'Failed to save changes');
    }
}

// SVG color update function
function updateSvgColor(svgContent) {
    if (!svgContent) return svgContent;
    return svgContent.replace(/fill="#000000"/g, 'fill="#ffd404"')
                    .replace(/fill='#000000'/g, "fill='#ffd404'")
                    .replace(/fill="#3498db"/g, 'fill="#ffd404"')
                    .replace(/fill='#3498db'/g, "fill='#ffd404'")
                    .replace(/fill="#10b981"/g, 'fill="#ffd404"')
                    .replace(/fill='#10b981'/g, "fill='#ffd404'")
                    .replace(/fill="#ffb800"/g, 'fill="#ffd404"')
                    .replace(/fill='#ffb800'/g, "fill='#ffd404'")
                    .replace(/fill="#FFFF00"/g, 'fill="#ffd404"')
                    .replace(/fill='#FFFF00'/g, "fill='#ffd404'");
}

// SVG preview update function
function updateSvgPreview(panelId) {
    const imageInput = document.getElementById(`${panelId}_image`);
    const previewContainer = document.getElementById(`${panelId}_svg_preview`);
    
    if (!imageInput || !previewContainer) return;
    
    const svgContent = imageInput.value.trim();
    if (!svgContent) {
        previewContainer.innerHTML = '';
        return;
    }
    
    try {
        // Update the preview with the SVG content
        previewContainer.innerHTML = updateSvgColor(svgContent);
    } catch (error) {
        console.error('Error updating SVG preview:', error);
        previewContainer.innerHTML = '<i class="fas fa-exclamation-circle" style="color: #ef4444;"></i>';
    }
}

// Panel sorting function
function sortPanels() {
    const panelsContainer = document.querySelector('.what-im-doing-grid');
    const panels = [...document.querySelectorAll('.what-im-doing-panel')];
    
    // Sort panels: enabled first, then disabled
    panels.sort((a, b) => {
        const aEnabled = a.querySelector('input[type="checkbox"]').checked;
        const bEnabled = b.querySelector('input[type="checkbox"]').checked;
        if (aEnabled === bEnabled) return 0;
        return aEnabled ? -1 : 1;
    });
    
    // Reorder in DOM
    panels.forEach(panel => panelsContainer.appendChild(panel));
    
    // Update panel numbers
    updatePanelNumbers();
}

// Initialize drag and drop for panels
function initializePanelDragAndDrop() {
    console.log('Initializing panel drag and drop');
    
    const panels = document.querySelectorAll('.what-im-doing-panel');
    
    // Add drag handles to each panel if they don't already have one
    panels.forEach(panel => {
        if (!panel.querySelector('.drag-handle')) {
            const dragHandle = document.createElement('div');
            dragHandle.className = 'drag-handle';
            dragHandle.innerHTML = '<i class="fas fa-grip-vertical"></i>';
            
            const panelHeader = panel.querySelector('.panel-header') || panel.firstElementChild;
            if (panelHeader) {
                panelHeader.insertBefore(dragHandle, panelHeader.firstChild);
            } else {
                panel.insertBefore(dragHandle, panel.firstChild);
            }
        }
        
        panel.setAttribute('draggable', 'true');
        
        // Remove existing event listeners to prevent duplicates
        panel.removeEventListener('dragstart', handlePanelDragStart);
        panel.removeEventListener('dragend', handlePanelDragEnd);
        panel.removeEventListener('dragover', handlePanelDragOver);
        panel.removeEventListener('drop', handlePanelDrop);
        
        // Add event listeners
        panel.addEventListener('dragstart', handlePanelDragStart);
        panel.addEventListener('dragend', handlePanelDragEnd);
        panel.addEventListener('dragover', handlePanelDragOver);
        panel.addEventListener('drop', handlePanelDrop);
    });
}

function handlePanelDragStart(e) {
    console.log('Panel drag started');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.panelId || this.id || '');
    
    this.classList.add('dragging');
    
    // Set a timer to make the panel visible again if drag fails
    setTimeout(() => {
        if (this.classList.contains('dragging')) {
            this.classList.remove('dragging');
        }
    }, 500);
}

function handlePanelDragEnd(e) {
    console.log('Panel drag ended');
    this.classList.remove('dragging');
    
    document.querySelectorAll('.what-im-doing-panel').forEach(panel => {
        panel.classList.remove('drag-over');
    });
    
    // Update all panel numbers
    updatePanelNumbers();
    
    // Save the new order
    saveAllChanges();
}

function handlePanelDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
    return false;
}

function handlePanelDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Panel dropped');
    this.classList.remove('drag-over');
    
    const draggedPanelId = e.dataTransfer.getData('text/plain');
    const draggedPanel = document.getElementById(draggedPanelId) || 
                         document.querySelector(`.what-im-doing-panel[data-panel-id="${draggedPanelId}"]`) || 
                         document.querySelector('.what-im-doing-panel.dragging');
    
    if (draggedPanel && this !== draggedPanel) {
        console.log('Reordering panels');
        const container = document.querySelector('.what-im-doing-container');
        
        // Get all panels to determine position
        const panels = Array.from(container.querySelectorAll('.what-im-doing-panel'));
        const targetIndex = panels.indexOf(this);
        const draggedIndex = panels.indexOf(draggedPanel);
        
        if (draggedIndex < targetIndex) {
            container.insertBefore(draggedPanel, this.nextElementSibling);
        } else {
            container.insertBefore(draggedPanel, this);
        }
        
        updatePanelNumbers();
    }
    
    return false;
}

function updatePanelNumbers() {
    console.log('Updating panel numbers');
    const panels = document.querySelectorAll('.what-im-doing-panel');
    panels.forEach((panel, index) => {
        panel.dataset.orderIndex = index + 1;
        const orderInput = panel.querySelector('input[name$="[order]"]');
        if (orderInput) {
            orderInput.value = index + 1;
        }
    });
}

// Initialize panel drag and drop on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up drag and drop');
    initializePanelDragAndDrop();
    
    // Set up an observer to reinitialize drag and drop for dynamically added panels
    const panelContainer = document.querySelector('.what-im-doing-container');
    if (panelContainer) {
        const observer = new MutationObserver(function(mutations) {
            console.log('Mutation observed in panel container');
            initializePanelDragAndDrop();
        });
        
        observer.observe(panelContainer, { 
            childList: true, 
            subtree: true 
        });
    }
}); 