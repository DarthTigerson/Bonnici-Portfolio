// Global variable to store portfolio projects
let portfolioProjects = [];
let showOnFrontend = true; // Default to showing portfolio on frontend
let originalShowOnFrontend = true; // Store the original value to detect changes
let columnsLayout = 2; // Default columns layout
let originalColumnsLayout = 2;
let displayMode = 'description'; // Default display mode (tags or description)
let originalDisplayMode = 'description';

// DOM elements
const projectModal = document.getElementById('project-modal');
const projectsList = document.getElementById('projects-list');
const projectForm = document.getElementById('project-form');
const projectsEnabledToggle = document.getElementById('projects-enabled');
const columnsSelect = document.getElementById('columns-select');
const displayModeSelect = document.getElementById('display-mode-select');
const projectIndexInput = document.getElementById('project-index');
const imagePreview = document.getElementById('image-preview');

// Load projects on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the projects from the server data
    const projectsListElement = document.getElementById('projects-list');
    if (projectsListElement) {
        const projectElements = projectsListElement.querySelectorAll('.project-card');
        portfolioProjects = Array.from(projectElements).map((item, index) => {
            const tagsElements = item.querySelectorAll('.project-tag');
            const tags = Array.from(tagsElements).map(tag => tag.textContent);
            
            // Get the image path and extract just the filename
            const imgElement = item.querySelector('img');
            let imagePath = '';
            let imageName = '';
            if (imgElement && imgElement.src) {
                imagePath = imgElement.src;
                // Extract the filename from the path
                imageName = imagePath.split('/').pop();
            }
            
            return {
                index: parseInt(item.dataset.id),
                title: item.querySelector('.project-title').textContent,
                tags: tags,
                description: item.querySelector('.project-description')?.textContent || '',
                image: imageName,
                image_url: imagePath,
                git_url: item.dataset.gitUrl || ''
                // Other properties will be loaded when editing
            };
        });
    }

    // Add core event listeners
    addCoreListeners();
    
    // Set up the options buttons
    setupOptionButtons();

    // Initialize projects toggle for frontend visibility
    if (projectsEnabledToggle) {
        // Get the initial value from the data attribute
        showOnFrontend = projectsEnabledToggle.checked;
        originalShowOnFrontend = showOnFrontend; // Store original value
        
        // Add event listener for the toggle
        projectsEnabledToggle.addEventListener('change', function() {
            showOnFrontend = this.checked;
            
            // Update toggle status indicator (but don't save to server yet)
            const toggleContainer = document.querySelector('.projects-toggle-container');
            if (toggleContainer) {
                if (showOnFrontend) {
                    toggleContainer.classList.add('is-enabled');
                    toggleContainer.classList.remove('is-disabled');
                    toggleContainer.querySelector('.toggle-label').textContent = 'Visible on frontend';
                } else {
                    toggleContainer.classList.add('is-disabled');
                    toggleContainer.classList.remove('is-enabled');
                    toggleContainer.querySelector('.toggle-label').textContent = 'Hidden on frontend';
                }
            }
            
            // If settings have been changed, highlight the save button
            if (showOnFrontend !== originalShowOnFrontend) {
                highlightSaveButton();
            }
        });
    }
    
    // Initialize columns select
    if (columnsSelect) {
        // Get the initial value
        columnsLayout = parseInt(columnsSelect.value);
        originalColumnsLayout = columnsLayout;
        
        // Add event listener
        columnsSelect.addEventListener('change', function() {
            columnsLayout = parseInt(this.value);
            
            // If settings have been changed, highlight the save button
            if (columnsLayout !== originalColumnsLayout) {
                highlightSaveButton();
            }
        });
    }
    
    // Initialize display mode select
    if (displayModeSelect) {
        // Get the initial value
        displayMode = displayModeSelect.value;
        originalDisplayMode = displayMode;
        
        // Add event listener
        displayModeSelect.addEventListener('change', function() {
            displayMode = this.value;
            
            // If settings have been changed, highlight the save button
            if (displayMode !== originalDisplayMode) {
                highlightSaveButton();
            }
        });
    }
    
    // Initialize file input for image upload
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Add direct event handler for Git URL test button
    const testGitUrlBtn = document.getElementById('test_git_url');
    if (testGitUrlBtn) {
        testGitUrlBtn.addEventListener('click', function(e) {
            // Explicitly stop propagation and prevent default
            if (e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
            }
            
            // Add a class to mark this as handled
            this.classList.add('handling-click');
            
            // Use a timeout to allow the class to be registered
            setTimeout(() => {
                const gitUrl = document.getElementById('git_url').value;
                if (gitUrl && gitUrl.trim() !== '') {
                    window.open(gitUrl, '_blank');
                } else {
                    alert('Please enter a Git URL first');
                }
                
                // Remove the handling class
                this.classList.remove('handling-click');
            }, 0);
            
            // Explicitly return false to prevent further handling
            return false;
        });
    }

    // Reset any existing confirmation flags to ensure clean state
    window.isConfirmingDelete = false;
});

// Add core event listeners for fixed UI elements
function addCoreListeners() {
    // Add New Project button
    const addSectionBtn = document.getElementById('addSectionBtn');
    if (addSectionBtn) {
        addSectionBtn.addEventListener('click', addNewSection);
    }
    
    // Save Settings button
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', savePortfolioSettings);
    }
    
    // Close modal button
    const closeModalBtn = document.getElementById('closeModalBtn');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }
    
    // Save project button in modal
    const saveProjectBtn = document.getElementById('save-project-btn');
    if (saveProjectBtn) {
        saveProjectBtn.addEventListener('click', saveProject);
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.options-menu')) {
            document.querySelectorAll('.options-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
    
    // Initialize drag-and-drop for project cards
    initializeProjectDragAndDrop();
}

// Set up options buttons with direct event handlers
function setupOptionButtons() {
    // Options buttons (three dots)
    document.querySelectorAll('.options-btn').forEach(button => {
        // First remove any existing listeners by cloning
        const newButton = button.cloneNode(true);
        if (button.parentNode) {
            button.parentNode.replaceChild(newButton, button);
        }
        
        // Add fresh click handler
        newButton.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.closest('.options-menu');
            
            // Close all other menus
            document.querySelectorAll('.options-menu.active').forEach(openMenu => {
                if (openMenu !== menu) {
                    openMenu.classList.remove('active');
                }
            });
            
            // Toggle this menu
            menu.classList.toggle('active');
        });
    });
    
    // Edit buttons
    document.querySelectorAll('.edit-project-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const projectId = this.getAttribute('data-id');
            editProject(parseInt(projectId));
        });
    });
    
    // Delete buttons
    document.querySelectorAll('.delete-project-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const projectId = this.getAttribute('data-id');
            deleteProject(parseInt(projectId));
        });
    });
    
    // Test URL buttons
    document.querySelectorAll('.test-url-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const projectId = this.getAttribute('data-id');
            testProjectLink(parseInt(projectId));
        });
    });
    
    // Prevent clicks inside dropdown from closing it
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
}

// Initialize drag and drop for projects
function initializeProjectDragAndDrop() {
    const projectCards = document.querySelectorAll('.project-card');
    
    projectCards.forEach(card => {
        // Remove existing event listeners to prevent duplicates
        card.removeEventListener('dragstart', handleProjectDragStart);
        card.removeEventListener('dragend', handleProjectDragEnd);
        card.removeEventListener('dragover', handleProjectDragOver);
        card.removeEventListener('dragenter', handleProjectDragEnter);
        card.removeEventListener('dragleave', handleProjectDragLeave);
        card.removeEventListener('drop', handleProjectDrop);
        
        // Add event listeners
        card.addEventListener('dragstart', handleProjectDragStart);
        card.addEventListener('dragend', handleProjectDragEnd);
        card.addEventListener('dragover', handleProjectDragOver);
        card.addEventListener('dragenter', handleProjectDragEnter);
        card.addEventListener('dragleave', handleProjectDragLeave);
        card.addEventListener('drop', handleProjectDrop);
    });
}

function handleProjectDragStart(e) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.id);
    
    this.classList.add('dragging');
    
    // Set a timer to make the card visible again if drag fails
    setTimeout(() => {
        if (this.classList.contains('dragging')) {
            this.classList.remove('dragging');
        }
    }, 500);
}

function handleProjectDragEnd(e) {
    this.classList.remove('dragging');
    
    document.querySelectorAll('.project-card').forEach(card => {
        card.classList.remove('drag-over');
    });
    
    // Update projects array based on current DOM order
    updateProjectsOrder();
    
    // Mark as needing save
    highlightSaveButton();
}

function handleProjectDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleProjectDragEnter(e) {
    e.preventDefault();
    this.classList.add('drag-over');
}

function handleProjectDragLeave(e) {
    this.classList.remove('drag-over');
}

function handleProjectDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    
    this.classList.remove('drag-over');
    
    const draggedProjectId = e.dataTransfer.getData('text/plain');
    const draggedCard = document.querySelector(`.project-card[data-id="${draggedProjectId}"]`);
    
    if (draggedCard && this !== draggedCard) {
        const projectsList = document.getElementById('projects-list');
        const cards = Array.from(projectsList.querySelectorAll('.project-card'));
        const targetIndex = cards.indexOf(this);
        const draggedIndex = cards.indexOf(draggedCard);
        
        console.log(`Dragged card ${draggedIndex} (${draggedCard.querySelector('.project-title').textContent}) to position ${targetIndex} (${this.querySelector('.project-title').textContent})`);
        
        if (draggedIndex < targetIndex) {
            projectsList.insertBefore(draggedCard, this.nextSibling);
        } else {
            projectsList.insertBefore(draggedCard, this);
        }
        
        // Update projects array based on new DOM order
        updateProjectsOrder();
        
        // Log new DOM order to verify
        const newOrder = Array.from(document.querySelectorAll('.project-card')).map(
            card => card.querySelector('.project-title').textContent
        );
        console.log("New DOM order after drop:", newOrder);
        
        // Mark as needing save
        highlightSaveButton();
    }
    
    return false;
}

// Update data-id attributes based on DOM order
function updateDataIds() {
    const projectCards = document.querySelectorAll('.project-card');
    
    console.log("Updating data-id attributes...");
    
    const beforeIds = Array.from(projectCards).map(card => {
        return {
            title: card.querySelector('.project-title').textContent,
            id: card.getAttribute('data-id')
        };
    });
    console.log("Before updating data-ids:", beforeIds);
    
    projectCards.forEach((card, index) => {
        // Update data-id attribute
        const oldId = card.getAttribute('data-id');
        card.setAttribute('data-id', index);
        
        // Update data-id in buttons
        card.querySelectorAll('button[data-id]').forEach(button => {
            button.setAttribute('data-id', index);
        });
    });
    
    const afterIds = Array.from(projectCards).map(card => {
        return {
            title: card.querySelector('.project-title').textContent,
            id: card.getAttribute('data-id')
        };
    });
    console.log("After updating data-ids:", afterIds);
}

// Update portfolio projects array based on current DOM order
function updateProjectsOrder() {
    const projectCards = document.querySelectorAll('.project-card');
    const newOrderedProjects = [];
    
    console.log("Before reordering, projects order:", portfolioProjects.map(p => p.title));
    
    projectCards.forEach((card, index) => {
        const oldIndex = parseInt(card.getAttribute('data-id'));
        const projectCopy = { ...portfolioProjects[oldIndex] };
        
        // Update the index property to match the new position
        projectCopy.index = index;
        
        newOrderedProjects.push(projectCopy);
    });
    
    console.log("After reordering, new projects order:", newOrderedProjects.map(p => p.title));
    
    // Replace the projects array with the newly ordered array
    portfolioProjects = newOrderedProjects;
    
    // Update data-id attributes
    updateDataIds();
}

// Add an event listener to add new project cards to DOM and make them draggable
document.addEventListener('DOMContentLoaded', function() {
    const projectsList = document.getElementById('projects-list');
    if (projectsList) {
        // Set up an observer to watch for changes to the projects list
        const observer = new MutationObserver(function(mutations) {
            initializeProjectDragAndDrop();
        });
        
        observer.observe(projectsList, { 
            childList: true, 
            subtree: true 
        });
    }
});

// This function should be called after adding new project to the DOM
function addProjectToUI(project, index) {
    // Check if "no projects" message is displayed and remove it
    const noProjectsMessage = document.querySelector('.no-projects');
    if (noProjectsMessage) {
        noProjectsMessage.remove();
    }
    
    // Create a new project card
    const projectCard = document.createElement('div');
    projectCard.className = 'project-card';
    projectCard.dataset.id = index;
    projectCard.dataset.gitUrl = project.git_url || '';
    projectCard.setAttribute('draggable', 'true');
    
    // Create drag handle
    const dragHandle = document.createElement('div');
    dragHandle.className = 'drag-handle';
    dragHandle.innerHTML = '<i class="fas fa-grip-vertical"></i>';
    projectCard.appendChild(dragHandle);
    
    // Create options menu
    const optionsMenu = document.createElement('div');
    optionsMenu.className = 'options-menu';
    
    const optionsButton = document.createElement('button');
    optionsButton.type = 'button';
    optionsButton.className = 'options-btn';
    optionsButton.setAttribute('aria-label', 'Options');
    optionsButton.innerHTML = '<i class="fas fa-ellipsis-v"></i>';
    
    // No need to add event listener here - handled by event delegation
    optionsMenu.appendChild(optionsButton);
    
    // Create dropdown menu
    const dropdownMenu = document.createElement('div');
    dropdownMenu.className = 'dropdown-menu';
    
    // Create dropdown items
    // Test URL button
    const testUrlButton = document.createElement('button');
    testUrlButton.type = 'button';
    testUrlButton.className = 'dropdown-item test-url-btn';
    testUrlButton.dataset.id = index;
    testUrlButton.title = 'Test URL';
    testUrlButton.innerHTML = '<i class="fas fa-flask"></i> Test URL';
    
    // No need to add event listener here - handled by event delegation
    
    // Edit button
    const editButton = document.createElement('button');
    editButton.type = 'button';
    editButton.className = 'dropdown-item edit-project-btn';
    editButton.dataset.id = index;
    editButton.innerHTML = '<i class="fas fa-edit"></i> Edit';
    
    // No need to add event listener here - handled by event delegation
    
    // Delete button
    const deleteButton = document.createElement('button');
    deleteButton.type = 'button';
    deleteButton.className = 'dropdown-item delete-project-btn';
    deleteButton.dataset.id = index;
    deleteButton.innerHTML = '<i class="fas fa-trash"></i> Delete';
    
    // No need to add event listener here - handled by event delegation
    
    // Add buttons to dropdown
    dropdownMenu.appendChild(testUrlButton);
    dropdownMenu.appendChild(editButton);
    dropdownMenu.appendChild(deleteButton);
    
    // Add dropdown to options menu
    optionsMenu.appendChild(dropdownMenu);
    
    // Add options menu to card
    projectCard.appendChild(optionsMenu);
    
    // Image container
    const imageContainer = document.createElement('div');
    imageContainer.className = 'project-card-image';
    
    const img = document.createElement('img');
    img.src = project.image_url || '/data/images/portfolio/default_image.webp';
    img.alt = project.title;
    imageContainer.appendChild(img);
    
    projectCard.appendChild(imageContainer);
    
    // Content container
    const contentContainer = document.createElement('div');
    contentContainer.className = 'project-card-content';
    
    const title = document.createElement('h5');
    title.className = 'project-title';
    title.textContent = project.title;
    contentContainer.appendChild(title);
    
    // Tags container
    const tagsContainer = document.createElement('div');
    tagsContainer.className = 'project-tags';
    
    if (project.tags && project.tags.length > 0) {
        project.tags.forEach(tag => {
            const tagSpan = document.createElement('span');
            tagSpan.className = 'project-tag';
            tagSpan.textContent = tag;
            tagsContainer.appendChild(tagSpan);
        });
    }
    
    contentContainer.appendChild(tagsContainer);
    
    // Description
    if (project.description) {
        const description = document.createElement('p');
        description.className = 'project-description';
        description.textContent = project.description;
        contentContainer.appendChild(description);
    }
    
    projectCard.appendChild(contentContainer);
    
    // Add to projects list
    projectsList.appendChild(projectCard);
    
    // Make the new card draggable
    projectCard.addEventListener('dragstart', handleProjectDragStart);
    projectCard.addEventListener('dragend', handleProjectDragEnd);
    projectCard.addEventListener('dragover', handleProjectDragOver);
    projectCard.addEventListener('dragenter', handleProjectDragEnter);
    projectCard.addEventListener('dragleave', handleProjectDragLeave);
    projectCard.addEventListener('drop', handleProjectDrop);
    
    // Setup option buttons for this new project
    setTimeout(() => {
        setupOptionButtons();
    }, 0);
    
    // Mark as needing save
    highlightSaveButton();
}

// Function to highlight the save button when changes are made
function highlightSaveButton() {
    const saveBtn = document.querySelector('.save-btn');
    if (saveBtn) {
        saveBtn.classList.add('needs-save');
    }
}

// Add New Section function
function addNewSection() {
    showAddProjectModal();
}

// Show Add Project Modal
function showAddProjectModal() {
    projectIndexInput.value = -1;
    projectForm.reset();
    imagePreview.src = '/data/images/portfolio/default_image.webp';
    projectModal.style.display = 'block';
}

// Close Modal
function closeModal() {
    projectModal.style.display = 'none';
}

// Edit Project
function editProject(index) {
    const project = portfolioProjects[index];
    if (!project) {
        showErrorNotification('Project not found');
        return;
    }
    
    projectIndexInput.value = index;
    
    // Load project data into form
    document.getElementById('title').value = project.title || '';
    document.getElementById('tags').value = project.tags ? project.tags.join(', ') : '';
    document.getElementById('description').value = project.description || '';
    document.getElementById('git_url').value = project.git_url || '';
    
    // Set image preview if available
    if (project.image_url) {
        imagePreview.src = project.image_url;
    } else {
        imagePreview.src = '/data/images/portfolio/default_image.webp';
    }
    
    // Show modal
    projectModal.style.display = 'block';
}

// Delete Project
function deleteProject(index) {
    // Prevent multiple dialog execution by checking if already confirming
    if (window.isConfirmingDelete) return;
    
    try {
        window.isConfirmingDelete = true;
        if (confirm('Are you sure you want to delete this project?')) {
            // Remove from UI first
            const projectElement = document.querySelector(`.project-card[data-id="${index}"]`);
            if (projectElement) {
                projectElement.remove();
            }
            
            // Remove from array
            portfolioProjects = portfolioProjects.filter((_, i) => i !== index);
            
            // Update data-id attributes to match new array indices
            updateDataIds();
            
            // Re-setup option buttons
            setTimeout(() => {
                setupOptionButtons();
            }, 0);
            
            // Show notification
            showSaveNotification('Project deleted successfully');
            
            // Mark as needing save
            highlightSaveButton();
        }
    } finally {
        // Always reset the flag, even if an error occurs
        window.isConfirmingDelete = false;
    }
}

// Save Project (Add or Update)
function saveProject() {
    // Validate form
    if (!projectForm.checkValidity()) {
        projectForm.reportValidity();
        return;
    }
    
    const index = parseInt(projectIndexInput.value);
    const isNewProject = index === -1;
    
    // Get form data
    const projectData = {
        title: document.getElementById('title').value,
        tags: document.getElementById('tags').value ? 
            document.getElementById('tags').value.split(',').map(item => item.trim()) : [],
        description: document.getElementById('description').value,
        git_url: document.getElementById('git_url').value
    };
    
    // Handle image preview URL
    if (isNewProject) {
        // For new projects, use default_image.webp if no image selected
        projectData.image = 'default_image.webp';
        projectData.image_url = '/data/images/portfolio/default_image.webp';
    } else {
        // For existing projects, keep the current image if no new one is selected
        projectData.image = portfolioProjects[index].image;
        projectData.image_url = portfolioProjects[index].image_url;
    }
    
    // Handle image upload
    const imageFile = document.getElementById('image').files[0];
    if (imageFile) {
        // We'll handle the actual upload when saving all projects
        projectData.newImage = imageFile;
        // Set a temporary preview URL
        projectData.image_url = imagePreview.src;
    }
    
    if (isNewProject) {
        // Add new project
        portfolioProjects.push(projectData);
        addProjectToUI(projectData, portfolioProjects.length - 1);
    } else {
        // Update existing project
        portfolioProjects[index] = { ...portfolioProjects[index], ...projectData };
        updateProjectInUI(projectData, index);
    }
    
    // Close modal
    closeModal();
    
    // Show notification
    showSaveNotification(isNewProject ? 'Project added successfully' : 'Project updated successfully');
    
    // Mark as needing save
    highlightSaveButton();
}

// Update Project in UI
function updateProjectInUI(project, index) {
    const projectCard = document.querySelector(`.project-card[data-id="${index}"]`);
    if (!projectCard) return;
    
    // Update title
    projectCard.querySelector('.project-title').textContent = project.title;
    
    // Update Git URL data attribute
    projectCard.dataset.gitUrl = project.git_url || '';
    
    // Update image if available
    if (project.image_url) {
        projectCard.querySelector('img').src = project.image_url;
    }
    
    // Update tags
    const tagsContainer = projectCard.querySelector('.project-tags');
    tagsContainer.innerHTML = '';
    if (project.tags && project.tags.length > 0) {
        project.tags.forEach(tag => {
            const tagSpan = document.createElement('span');
            tagSpan.className = 'project-tag';
            tagSpan.textContent = tag;
            tagsContainer.appendChild(tagSpan);
        });
    }
    
    // Update description
    projectCard.querySelector('.project-description').textContent = project.description || '';
    
    // Setup option buttons again to ensure they work
    setTimeout(() => {
        setupOptionButtons();
    }, 0);
    
    // Mark as needing save
    highlightSaveButton();
}

// Save Portfolio Settings
async function savePortfolioSettings() {
    try {
        // Prepare data for saving
        const portfolioData = {
            enabled: showOnFrontend,
            columns: columnsLayout,
            mode: displayMode,
            projects: portfolioProjects.map((project, arrayIndex) => {
                // Create a clean project object without temporary UI properties
                const cleanProject = {
                    // Use actual position in the array (not the stored index property)
                    index: arrayIndex + 1, // Ensure index starts from 1 for backend
                    title: project.title,
                    tags: project.tags,
                    description: project.description,
                    image: project.image  // Include image name
                };
                
                // Add optional properties if they exist
                if (project.git_url) cleanProject.git_url = project.git_url;
                
                return cleanProject;
            })
        };
        
        // Log the order we're saving
        console.log('Saving projects with order:', portfolioData.projects.map(p => p.title));
        
        // Create FormData object for file uploads
        const formData = new FormData();
        formData.append('data', JSON.stringify(portfolioData));
        
        // Add any images that need to be uploaded
        portfolioProjects.forEach((project, index) => {
            if (project.newImage) {
                formData.append(`image_${index}`, project.newImage);
            }
        });
        
        // Send data to server
        const response = await fetch('/portfolio/save', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to save portfolio settings');
        }
        
        const data = await response.json();
            
        if (data.success) {
            // Update original values to reflect saved state
            originalShowOnFrontend = showOnFrontend;
            originalColumnsLayout = columnsLayout;
            originalDisplayMode = displayMode;
            
            // Remove needs-save class from save button
            const saveBtn = document.querySelector('.save-btn');
            if (saveBtn) {
                saveBtn.classList.remove('needs-save');
            }
            
            // Show success notification
            showSaveNotification('Portfolio settings saved successfully!');
        } else {
            throw new Error(data.message || 'Failed to save portfolio settings');
        }
    } catch (error) {
        console.error('Error saving portfolio settings:', error);
        showErrorNotification(error.message || 'Failed to save portfolio settings');
    }
}

// Show Success Notification
function showSaveNotification(message = 'Portfolio settings saved successfully!') {
    const notification = document.createElement('div');
    notification.className = 'save-notification';
    notification.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Show Error Notification
function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Init Portfolio
function initPortfolio() {
    // Load portfolio settings
    fetch('/admin/api/portfolio/settings')
        .then(response => response.json())
        .then(data => {
            // Set columns layout
            columnsLayout = data.columns_layout || 3;
            document.getElementById(`columns-${columnsLayout}`).classList.add('active');
            
            // Set display mode
            displayMode = data.display_mode || 'grid';
            document.getElementById(`display-${displayMode}`).classList.add('active');
            projectsList.classList.add(`display-${displayMode}`);
            
            // Set visibility
            const showOnFrontend = data.show_on_frontend || false;
            visibilityToggle.checked = showOnFrontend;
            
            // Update UI based on settings
            updateLayoutStyle();
        })
        .catch(error => {
            console.error('Error loading portfolio settings:', error);
            showNotification('Error loading portfolio settings', 'error');
        });
    
    // Load projects
    fetch('/admin/api/portfolio/projects')
        .then(response => response.json())
        .then(data => {
            projects = data;
            
            if (projects.length === 0) {
                projectsList.innerHTML = '<div class="no-projects">No projects added yet.</div>';
            } else {
                projects.forEach((project, index) => {
                    addProjectToUI(project, index);
                });
                
                // Add event listeners to project cards
                document.querySelectorAll('.edit-project-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const projectId = parseInt(this.dataset.id);
                        editProject(projectId);
                    });
                });
                
                document.querySelectorAll('.delete-project-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const projectId = parseInt(this.dataset.id);
                        deleteProject(projectId);
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error loading projects:', error);
            showNotification('Error loading projects', 'error');
        });
}

// Test Project Link
function testProjectLink(index) {
    // Skip execution if the click came from the manual Git URL test button
    if (event && event.target && (event.target.id === 'test_git_url' || event.target.closest('#test_git_url'))) {
        return;
    }
    
    const project = portfolioProjects[index];
    if (!project) {
        showErrorNotification('Project not found');
        return;
    }
    
    if (project.git_url) {
        window.open(project.git_url, '_blank');
    } else {
        showErrorNotification('No Git URL available for this project');
    }
}

