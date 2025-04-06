// Message Modal Functionality
const modal = document.getElementById("messageModal");
const closeBtn = document.getElementsByClassName("close")[0];
const unreadBtn = document.getElementById("unreadBtn");
const deleteBtn = document.getElementById("deleteBtn");
let currentMessageId = null;

// Close modal when clicking the X
closeBtn.onclick = function() {
    modal.style.display = "none";
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Function to view a message
function viewMessage(messageId) {
    currentMessageId = messageId;
    
    // Fetch message details
    fetch(`/messages/${messageId}`)
        .then(response => response.json())
        .then(data => {
            // Update modal content
            document.getElementById("modalSender").textContent = data.fullname;
            document.getElementById("modalEmail").textContent = data.email;
            document.getElementById("modalSubject").textContent = data.subject;
            document.getElementById("modalMessage").textContent = data.message;
            
            // Update meta information
            document.getElementById("modalIpAddress").textContent = data.ip_address || "-";
            document.getElementById("modalCountry").textContent = data.country || "-";
            document.getElementById("modalCity").textContent = data.city || "-";
            
            // Format date
            const date = new Date(data.created);
            document.getElementById("modalDate").textContent = date.toLocaleString();
            
            // Load map if coordinates are available
            const mapContainer = document.getElementById("modalMap");
            mapContainer.innerHTML = ""; // Clear previous map
            
            if (data.latitude && data.longitude) {
                const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${data.longitude-0.1}%2C${data.latitude-0.1}%2C${data.longitude+0.1}%2C${data.latitude+0.1}&layer=mapnik&marker=${data.latitude}%2C${data.longitude}`;
                const iframe = document.createElement("iframe");
                iframe.src = mapUrl;
                iframe.width = "100%";
                iframe.height = "300";
                iframe.frameBorder = "0";
                iframe.scrolling = "no";
                iframe.marginHeight = "0";
                iframe.marginWidth = "0";
                mapContainer.appendChild(iframe);
            } else {
                mapContainer.innerHTML = "<p>Location data not available</p>";
            }
            
            // Show modal
            modal.style.display = "block";
            
            // Mark as read if it was unread
            if (!data.viewed) {
                fetch(`/messages/${messageId}/read`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "success") {
                        // Update UI to reflect read status
                        const row = document.querySelector(`tr[data-id="${messageId}"]`);
                        if (row) {
                            row.classList.remove("unread");
                        }
                    }
                })
                .catch(error => console.error("Error marking message as read:", error));
            }
        })
        .catch(error => console.error("Error fetching message:", error));
}

// Mark as unread button
unreadBtn.onclick = function() {
    if (currentMessageId) {
        fetch(`/messages/${currentMessageId}/unread`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                // Update UI to reflect unread status
                const row = document.querySelector(`tr[data-id="${currentMessageId}"]`);
                if (row) {
                    row.classList.add("unread");
                }
                // Close the modal without notification
                modal.style.display = "none";
            }
        })
        .catch(error => console.error("Error marking message as unread:", error));
    }
}

// Delete button
deleteBtn.onclick = function() {
    if (currentMessageId) {
        if (confirm("Are you sure you want to delete this message? This action cannot be undone.")) {
            fetch(`/messages/${currentMessageId}/delete`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    // Remove the row from the table
                    const row = document.querySelector(`tr[data-id="${currentMessageId}"]`);
                    if (row) {
                        row.remove();
                    }
                    // Close the modal
                    modal.style.display = "none";
                }
            })
            .catch(error => console.error("Error deleting message:", error));
        }
    }
}

// Delete All Messages button
const deleteAllBtn = document.getElementById("deleteAllBtn");

deleteAllBtn.onclick = function() {
    if (confirm("Are you sure you want to delete ALL messages? This action cannot be undone.")) {
        fetch('/messages/all', {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                // Remove all rows from the table
                const tbody = document.querySelector('.messages-table tbody');
                tbody.innerHTML = '';
            }
        })
        .catch(error => console.error("Error deleting all messages:", error));
    }
}

// View Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const toggleButtons = document.querySelectorAll('.view-toggle-btn');
    const viewContents = document.querySelectorAll('.view-content');
    let visitorsChart = null;

    toggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetView = button.getAttribute('data-view');
            
            // Update button states
            toggleButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update view content
            viewContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `visitors-${targetView}-view`) {
                    content.classList.add('active');
                    if (targetView === 'chart' && !visitorsChart) {
                        initializeChart();
                    }
                }
            });
        });
    });

    function initializeChart() {
        const ctx = document.getElementById('visitorsChart').getContext('2d');
        const dates = Array.from(document.querySelectorAll('.visitors-table tbody tr')).map(
            row => row.querySelector('td:first-child').textContent
        ).reverse();
        
        // Count visits per date
        const visitCounts = {};
        dates.forEach(date => {
            visitCounts[date] = (visitCounts[date] || 0) + 1;
        });

        visitorsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(visitCounts),
                datasets: [{
                    label: 'Visits per Day',
                    data: Object.values(visitCounts),
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: (tooltipItems) => {
                                return tooltipItems[0].label;
                            },
                            label: (context) => {
                                const visits = context.parsed.y;
                                return `${visits} visit${visits !== 1 ? 's' : ''}`;
                            }
                        }
                    }
                }
            }
        });
    }
}); 