document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authForms = document.getElementById("auth-forms");
  const registerForm = document.getElementById("register-form");
  const loginForm = document.getElementById("login-form");
  const verifyForm = document.getElementById("verify-form");
  const logoutButton = document.getElementById("logout-button");
  const accountStatus = document.getElementById("account-status");
  const authMessage = document.getElementById("auth-message");
  const signupAccountNote = document.getElementById("signup-account-note");

  let currentUser = null;

  function showAuthMessage(message, className = "info") {
    authMessage.textContent = message;
    authMessage.className = className;
  }

  function updateAccountView(user) {
    currentUser = user;
    const loggedIn = Boolean(user);
    authForms.classList.toggle("hidden", loggedIn);
    logoutButton.classList.toggle("hidden", !loggedIn);
    accountStatus.classList.toggle("hidden", !loggedIn);
    verifyForm.classList.toggle("hidden", !loggedIn || user.email_verified);
    signupAccountNote.textContent = loggedIn
      ? `Signed in as ${user.email} (${user.school})`
      : "Log in to sign up for an activity.";
    signupForm.querySelector("button[type=submit]").disabled = !loggedIn;

    if (loggedIn) {
      accountStatus.textContent = `${user.full_name} | ${user.grade_level} | ${user.school}`;
      if (!user.email_verified) {
        showAuthMessage("Verify your email before managing organizations.", "info");
      }
    }
  }

  async function sendAuthRequest(url, options) {
    const response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || "Authentication request failed");
    }
    return result;
  }

  async function loadCurrentUser() {
    const response = await fetch("/auth/me");
    if (response.ok) {
      updateAccountView(await response.json());
    } else {
      updateAccountView(null);
    }
  }

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const result = await sendAuthRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: document.getElementById("full-name").value,
          grade_level: document.getElementById("grade-level").value,
          email: document.getElementById("register-email").value,
          password: document.getElementById("register-password").value,
        }),
      });
      updateAccountView(result.user);
      document.getElementById("verification-token").value = result.verification_token;
      showAuthMessage(result.message, "success");
      registerForm.reset();
    } catch (error) {
      showAuthMessage(error.message, "error");
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const result = await sendAuthRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: document.getElementById("login-email").value,
          password: document.getElementById("login-password").value,
        }),
      });
      updateAccountView(result.user);
      showAuthMessage(result.message, "success");
      loginForm.reset();
    } catch (error) {
      showAuthMessage(error.message, "error");
    }
  });

  verifyForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const result = await sendAuthRequest("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token: document.getElementById("verification-token").value }),
      });
      updateAccountView(result.user);
      showAuthMessage(result.message, "success");
      verifyForm.reset();
    } catch (error) {
      showAuthMessage(error.message, "error");
    }
  });

  logoutButton.addEventListener("click", async () => {
    await fetch("/auth/logout", { method: "POST" });
    updateAccountView(null);
    showAuthMessage("Logged out successfully", "success");
  });

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  loadCurrentUser();
  fetchActivities();
});
