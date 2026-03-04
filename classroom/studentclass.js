// CodeTracker - GitHub Project Tracking System
document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const logoIcon = document.querySelector(".logo-icon");
  const assignmentTitles = document.querySelectorAll(".assignment-title");
  const newSubmissionBtn = document.getElementById("newSubmissionBtn");
  const viewAllActivityBtn = document.getElementById("viewAllActivityBtn");
  const daysLeftElements = document.querySelectorAll(
    ".days-left, .deadline-date",
  );

  // Initialize the dashboard
  initDashboard();

  // API Base URL
  const API_BASE_URL = "http://localhost:3000";

  function initDashboard() {
    console.log("CodeTracker Dashboard Initialized");

    // Update days left counters
    updateDaysLeft();

    // Set up event listeners
    setupEventListeners();

    // Add click effect to logo
    if (logoIcon) {
      logoIcon.style.cursor = "pointer";
      logoIcon.title = "CodeTracker - GitHub Project Tracking System";
    }

    // Load instructor feedback from server
    loadInstructorFeedback();

    // Show welcome notification
    showNotification(
      "Welcome to CodeTracker! Dashboard loaded successfully.",
      "info",
    );
  }

  // Load instructor feedback from server
  async function loadInstructorFeedback() {
    try {
      const response = await fetch(`${API_BASE_URL}/get-all-feedback`);
      const data = await response.json();

      if (data.success && data.feedback) {
        // Loop through each assignment's feedback
        for (const [assignmentId, feedbackList] of Object.entries(data.feedback)) {
          displayFeedbackForAssignment(assignmentId, feedbackList);
        }
      }
    } catch (error) {
      console.log("No feedback available yet or server not running");
    }
  }

  // Display feedback for a specific assignment
  function displayFeedbackForAssignment(assignmentId, feedbackList) {
    const feedbackEl = document.getElementById(`feedback-${assignmentId}`);
    if (!feedbackEl) return;

    // Calculate totals
    let totalErrors = 0;
    let totalWarnings = 0;
    let latestFeedback = null;

    feedbackList.forEach((fb) => {
      totalErrors += fb.errors ? fb.errors.length : 0;
      totalWarnings += fb.warnings ? fb.warnings.length : 0;
      if (!latestFeedback || new Date(fb.timestamp) > new Date(latestFeedback.timestamp)) {
        latestFeedback = fb;
      }
    });

    // Update error/warning counts
    const errorCountEl = feedbackEl.querySelector(".error-count");
    const warningCountEl = feedbackEl.querySelector(".warning-count");
    if (errorCountEl) errorCountEl.textContent = totalErrors;
    if (warningCountEl) warningCountEl.textContent = totalWarnings;

    // Update timestamp
    const timestampEl = feedbackEl.querySelector(".feedback-timestamp");
    if (timestampEl && latestFeedback) {
      const date = new Date(latestFeedback.timestamp);
      timestampEl.textContent = date.toLocaleDateString() + " " + date.toLocaleTimeString();
    }

    // Update feedback message
    const messageEl = feedbackEl.querySelector(".feedback-message");
    if (messageEl && latestFeedback && latestFeedback.feedback) {
      messageEl.textContent = latestFeedback.feedback;
    }

    // Generate detailed feedback content
    const detailsEl = feedbackEl.querySelector(".feedback-details");
    if (detailsEl) {
      let detailsHtml = "";
      
      feedbackList.forEach((fb) => {
        if (fb.errors && fb.errors.length > 0) {
          fb.errors.forEach((err) => {
            detailsHtml += `<div class="feedback-item error">
              <i class="fas fa-times-circle"></i>
              <span class="file-name">${fb.file_path}</span>
              <span class="line-num">Line ${err.line}</span>
              <span class="message">${err.message}</span>
            </div>`;
          });
        }
        if (fb.warnings && fb.warnings.length > 0) {
          fb.warnings.forEach((warn) => {
            detailsHtml += `<div class="feedback-item warning">
              <i class="fas fa-exclamation-triangle"></i>
              <span class="file-name">${fb.file_path}</span>
              <span class="line-num">Line ${warn.line}</span>
              <span class="message">${warn.message}</span>
            </div>`;
          });
        }
      });
      
      detailsEl.innerHTML = detailsHtml;
    }

    // Show the feedback section
    feedbackEl.style.display = "block";

    // Add activity for feedback received
    addFeedbackActivity();
  }

  // Add feedback activity to activity list
  function addFeedbackActivity() {
    const activityList = document.querySelector(".activity-list");
    if (!activityList) return;

    // Check if feedback activity already exists
    const existingFeedback = activityList.querySelector('[data-activity="feedback"]');
    if (existingFeedback) return;

    // Create new feedback activity item
    const feedbackActivity = document.createElement("div");
    feedbackActivity.className = "activity-item";
    feedbackActivity.setAttribute("data-activity", "feedback");
    feedbackActivity.innerHTML = `
      <div class="activity-avatar accent-bg">
        <i class="fas fa-comment"></i>
      </div>
      <div class="activity-content">
        <div class="activity-text">
          Instructor feedback received on System 1
        </div>
        <div class="activity-meta">
          <span class="activity-time">Just now</span>
          <span class="label label-blue">Feedback</span>
        </div>
      </div>
    `;

    // Insert at the top of activity list
    activityList.insertBefore(feedbackActivity, activityList.firstChild);
  }

  function setupEventListeners() {
    // Logo click event
    if (logoIcon) {
      logoIcon.addEventListener("click", showCodeTrackerInfo);
    }

    // Assignment title click events
    assignmentTitles.forEach((title) => {
      title.addEventListener("click", function (e) {
        e.preventDefault();
        const assignmentName = this.textContent.trim();
        showNotification(`Viewing assignment: ${assignmentName}`, "info");
      });
    });

    // Button click events
    if (newSubmissionBtn) {
      newSubmissionBtn.addEventListener("click", function (e) {
        e.preventDefault();
        showNotification("Opening new submission form...", "info");
        // In a real app, this would open a modal or navigate to submission page
      });
    }

    if (viewAllActivityBtn) {
      viewAllActivityBtn.addEventListener("click", function (e) {
        e.preventDefault();
        showNotification("Loading all activity...", "info");
        // In a real app, this would load more activity items
      });
    }

    // Add hover effects to cards
    const cards = document.querySelectorAll(".card");
    cards.forEach((card) => {
      card.addEventListener("mouseenter", function () {
        this.style.transform = "translateY(-4px)";
        this.style.boxShadow = "0 8px 24px rgba(0, 0, 0, 0.2)";
      });

      card.addEventListener("mouseleave", function () {
        this.style.transform = "translateY(0)";
        this.style.boxShadow = "none";
      });
    });

    // Add click effect to activity items
    const activityItems = document.querySelectorAll(".activity-item");
    activityItems.forEach((item) => {
      item.addEventListener("click", function () {
        const activityText = this.querySelector(".activity-text").textContent;
        showNotification(`Activity: ${activityText}`, "info");
      });

      item.style.cursor = "pointer";
    });
  }
  // View All Activity Modal (SYNC VERSION)
  const activityModal = document.getElementById("activityModal");
  const openActivityBtn = document.getElementById("viewAllActivityBtn");
  const closeActivityBtn = document.getElementById("closeActivityModal");

  openActivityBtn.addEventListener("click", function (e) {
    e.preventDefault();

    // Get original activity list
    const originalActivityList = document.querySelector(".activity-list");

    // Get modal container
    const modalActivityContainer = document.querySelector(".all-activity-list");

    // Clone activity list
    modalActivityContainer.innerHTML = originalActivityList.innerHTML;

    activityModal.style.display = "block";
  });

  closeActivityBtn.addEventListener("click", function () {
    activityModal.style.display = "none";
  });

  window.addEventListener("click", function (e) {
    if (e.target === activityModal) {
      activityModal.style.display = "none";
    }
  });
  function updateDaysLeft() {
    const today = new Date();
    const dueDate = new Date("2026-02-15");
    const timeDiff = dueDate.getTime() - today.getTime();
    const daysLeft = Math.ceil(timeDiff / (1000 * 3600 * 24));

    // Update all days left elements
    daysLeftElements.forEach((element) => {
      if (element.classList.contains("days-left")) {
        element.textContent = `${daysLeft} days left`;
      } else if (element.textContent.includes("9 days")) {
        element.textContent = `Due Feb 15, 2026 (${daysLeft} days)`;
      } else if (element.textContent.includes("14 days")) {
        const quizDueDate = new Date("2026-02-20");
        const quizDaysLeft = Math.ceil(
          (quizDueDate.getTime() - today.getTime()) / (1000 * 3600 * 24),
        );
        element.textContent = `Due Feb 20, 2026 (${quizDaysLeft} days)`;
      } else if (element.textContent.includes("23 days")) {
        const projectDueDate = new Date("2026-03-01");
        const projectDaysLeft = Math.ceil(
          (projectDueDate.getTime() - today.getTime()) / (1000 * 3600 * 24),
        );
        element.textContent = `Due Mar 1, 2026 (${projectDaysLeft} days)`;
      }
    });

    // Update urgent label if less than 3 days left
    const urgentLabel = document.querySelector(".label-red");
    if (daysLeft <= 3 && urgentLabel) {
      urgentLabel.innerHTML = `<i class="fas fa-exclamation-triangle"></i> URGENT (${daysLeft} days)`;
    }
  }

  function showCodeTrackerInfo() {
    const info = `
            CodeTracker v1.0
            GitHub Project Tracking System
            Developed by Dexter Facelo
            SE1-2026 Project
            Last Updated: ${new Date().toLocaleDateString()}
        `;

    showNotification(info, "info");

    // Add visual feedback
    logoIcon.style.transform = "scale(1.1)";
    setTimeout(() => {
      logoIcon.style.transform = "scale(1)";
    }, 300);
  }

  function showNotification(message, type = "info") {
    // Remove existing notification
    const existingNotification = document.querySelector(".notification");
    if (existingNotification) {
      existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;

    // Create notification dot
    const dot = document.createElement("div");
    dot.className = "notification-dot";
    dot.style.backgroundColor =
      type === "success"
        ? "var(--color-success-fg)"
        : type === "error"
          ? "var(--color-danger-fg)"
          : "var(--color-accent-fg)";

    // Create message container
    const messageDiv = document.createElement("div");
    messageDiv.textContent = message;

    // Assemble notification
    notification.appendChild(dot);
    notification.appendChild(messageDiv);

    // Add to document
    document.body.appendChild(notification);

    // Auto-remove after 4 seconds
    setTimeout(() => {
      notification.style.animation = "slideOutRight 0.3s ease-out forwards";
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 300);
    }, 4000);
  }

  // Simulate real-time updates
  function simulateUpdates() {
    setInterval(() => {
      // Randomly update progress bars occasionally
      if (Math.random() > 0.7) {
        const progressItems = document.querySelectorAll(".progress-fill");
        progressItems.forEach((item) => {
          const currentWidth = parseInt(item.style.width);
          const randomChange = Math.random() > 0.5 ? 1 : -1;
          const newWidth = Math.max(
            10,
            Math.min(100, currentWidth + randomChange),
          );
          item.style.width = `${newWidth}%`;

          // Update corresponding value
          const progressValue = item
            .closest(".progress-item")
            .querySelector(".progress-value");
          if (progressValue) {
            if (progressValue.textContent.includes("/")) {
              const [current, total] = progressValue.textContent
                .split("/")
                .map(Number);
              const newCurrent = Math.max(
                0,
                Math.min(total, current + randomChange),
              );
              progressValue.textContent = `${newCurrent}/${total}`;
            } else if (progressValue.textContent.includes("%")) {
              const currentPercent = parseInt(progressValue.textContent);
              const newPercent = Math.max(
                0,
                Math.min(100, currentPercent + randomChange),
              );
              progressValue.textContent = `${newPercent}%`;
            }
          }
        });

        showNotification("Progress updated automatically", "info");
      }
    }, 15000); // Every 15 seconds
  }

  // Start simulation after initial load
  setTimeout(simulateUpdates, 5000);

  // Add keyboard shortcuts
  document.addEventListener("keydown", function (e) {
    // Ctrl + H for help
    if (e.ctrlKey && e.key === "h") {
      e.preventDefault();
      showCodeTrackerInfo();
    }

    // Ctrl + D for dashboard refresh
    if (e.ctrlKey && e.key === "d") {
      e.preventDefault();
      updateDaysLeft();
      showNotification("Dashboard data refreshed", "success");
    }

    // Escape to close notifications
    if (e.key === "Escape") {
      const notification = document.querySelector(".notification");
      if (notification) {
        notification.remove();
      }
    }
  });

  // Add context menu to logo
  if (logoIcon) {
    logoIcon.addEventListener("contextmenu", function (e) {
      e.preventDefault();
      showNotification(
        "Right-click: CodeTracker Admin Options (Simulated)",
        "info",
      );
    });
  }

  // Initialize tooltips
  function initTooltips() {
    const elementsWithTooltips = [
      { selector: ".user-avatar", text: "Your Profile" },
      { selector: ".course-icon", text: "Course Details" },
      { selector: ".btn-primary", text: "Create New Item" },
      { selector: ".label", text: "Status Label" },
    ];

    elementsWithTooltips.forEach((item) => {
      const element = document.querySelector(item.selector);
      if (element) {
        element.title = item.text;
      }
    });
  }

  initTooltips();
});
// Get elements
const modal = document.getElementById("submissionModal");
const openBtn = document.getElementById("newSubmissionBtn");
const closeBtn = document.getElementById("closeModal");
const form = document.getElementById("submissionForm");

// Open modal
openBtn.addEventListener("click", function (e) {
  e.preventDefault();
  modal.style.display = "block";
});

// Close modal
closeBtn.addEventListener("click", function () {
  modal.style.display = "none";
});

// Close when clicking outside
window.addEventListener("click", function (e) {
  if (e.target === modal) {
    modal.style.display = "none";
  }
});

// Handle form submit
form.addEventListener("submit", function (e) {
  e.preventDefault();

  const project = document.getElementById("projectSelect").value;
  const github = document.getElementById("repositorySelect").value;

  const note = document.getElementById("submissionNote").value;

  if (!project || !github) {
    alert("Please complete all required fields.");
    return;
  }

  alert(
    `Submission Successful!\n\nProject: ${project}\nGitHub: ${github}\nNote: ${note}`,
  );

  form.reset();
  modal.style.display = "none";
});
