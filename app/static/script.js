(() => {
  "use strict";

  // Apply theme before the page renders.
  const root = document.documentElement;
  const preference = window.matchMedia("(prefers-color-scheme: dark)");

  let savedTheme;

  try {
    savedTheme = localStorage.getItem("policymate-theme");
  } catch {}

  let explicitTheme = savedTheme === "dark" || savedTheme === "light";

  root.dataset.theme = explicitTheme
    ? savedTheme
    : preference.matches
      ? "dark"
      : "light";

  document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);

    // Topic shortcuts based on your company policy categories.
    const topics = [
      {
        name: "Employee Conduct",
        icon: "people",
        questions: [
          "What standards of conduct must employees follow?",
          "What behavior is prohibited at work?",
        ],
      },
      {
        name: "Attendance & Working Hours",
        icon: "clock",
        questions: [
          "What are the working hours?",
          "How should employees report a late arrival or absence?",
        ],
      },
      {
        name: "Leave Management",
        icon: "calendar",
        questions: [
          "What types of leave can employees request?",
          "How can I apply for leave?",
        ],
      },
      {
        name: "Remote Work",
        icon: "home",
        questions: [
          "What is the remote work policy?",
          "What responsibilities apply when working remotely?",
        ],
      },
      {
        name: "Data Protection",
        icon: "shield",
        questions: [
          "How should employees protect confidential company information?",
          "What are the rules for sharing company data?",
        ],
      },
      {
        name: "IT Usage",
        icon: "laptop",
        questions: [
          "What are the rules for using company technology?",
          "What does the IT usage policy say about personal use?",
        ],
      },
      {
        name: "Performance Management",
        icon: "chart",
        questions: [
          "How is employee performance evaluated?",
          "What does the policy say about employee development?",
        ],
      },
      {
        name: "Health & Safety",
        icon: "safety",
        questions: [
          "What workplace health and safety rules must employees follow?",
          "How should employees report workplace hazards?",
        ],
      },
      {
        name: "Conflict of Interest",
        icon: "balance",
        questions: [
          "What is considered a conflict of interest?",
          "How should employees disclose a conflict of interest?",
        ],
      },
    ];

    const mobile = window.matchMedia("(max-width: 900px)");

    let menuOpen = false;
    let busy = false;
    let lastAnswer = "";

    function icon(name) {
      const namespace = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(namespace, "svg");
      const use = document.createElementNS(namespace, "use");

      svg.setAttribute("class", "icon");
      svg.setAttribute("aria-hidden", "true");
      use.setAttribute("href", `#${name}`);

      svg.append(use);

      return svg;
    }

    function node(tag, className, text) {
      const element = document.createElement(tag);
      element.className = className;

      if (text !== undefined) {
        element.textContent = text;
      }

      return element;
    }

    function status(text, error = false) {
      $("status").textContent = text;
      $("status").dataset.error = String(error);
    }

    // Theme
    function syncTheme() {
      const dark = root.dataset.theme === "dark";

      $("theme-toggle").textContent = dark ? "Light mode" : "Dark mode";
      $("theme-toggle").setAttribute("aria-pressed", String(dark));
      $("theme-toggle").setAttribute(
        "aria-label",
        `Switch to ${dark ? "light" : "dark"} mode`
      );
    }

    $("theme-toggle").addEventListener("click", () => {
      root.dataset.theme =
        root.dataset.theme === "dark" ? "light" : "dark";

      explicitTheme = true;

      try {
        localStorage.setItem("policymate-theme", root.dataset.theme);
      } catch {}

      syncTheme();
    });

    preference.addEventListener("change", (event) => {
      if (!explicitTheme) {
        root.dataset.theme = event.matches ? "dark" : "light";
        syncTheme();
      }
    });

    syncTheme();

    // Mobile sidebar
    function setMenu(open, restoreFocus = true) {
      menuOpen = mobile.matches && open;

      $("sidebar").classList.toggle("is-open", menuOpen);
      $("sidebar").inert = mobile.matches && !menuOpen;
      $("main-shell").inert = menuOpen;
      $("backdrop").hidden = !menuOpen;

      document.body.classList.toggle("menu-open", menuOpen);

      $("open-menu").setAttribute(
        "aria-expanded",
        String(menuOpen)
      );

      if (menuOpen) {
        $("close-menu").focus();
      } else if (restoreFocus && mobile.matches) {
        $("open-menu").focus();
      }
    }

    $("open-menu").addEventListener("click", () => setMenu(true));
    $("close-menu").addEventListener("click", () => setMenu(false));
    $("backdrop").addEventListener("click", () => setMenu(false));

    mobile.addEventListener("change", () => {
      setMenu(false, false);
    });

    document.addEventListener("keydown", (event) => {
      if (!menuOpen) return;

      if (event.key === "Escape") {
        event.preventDefault();
        setMenu(false);
      }

      if (event.key !== "Tab") return;

      const items = [
        ...$("sidebar").querySelectorAll(
          "a[href], button:not(:disabled)"
        ),
      ];

      const first = items[0];
      const last = items[items.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    setMenu(false, false);

    // Quick question cards
    function renderQuick(topic) {
      $("quick-grid").replaceChildren();

      const selections = topic
        ? topic.questions.map((question) => ({ topic, question }))
        : [topics[2], topics[1], topics[4], topics[3]].map((item) => ({
            topic: item,
            question: item.questions[0],
          }));

      $("quick-title").textContent = topic
        ? `${topic.name} questions`
        : "Quick questions";

      for (const item of selections) {
        const button = node("button", "quick-card");
        button.type = "button";
        button.disabled = busy;

        const badge = node("span", "quick-icon");
        badge.append(icon(item.topic.icon));

        const label = node("span", "min-w-0");

        label.append(
          node("strong", "", item.question),
          node("small", "", item.topic.name)
        );

        button.append(badge, label);

        button.addEventListener("click", () => {
          if (busy) return;

          $("question").value = item.question;
          $("ask-form").requestSubmit();
        });

        $("quick-grid").append(button);
      }
    }

    // Sidebar categories
    [null, ...topics].forEach((topic, index) => {
      const button = node("button", "category-button");
      button.type = "button";

      button.setAttribute("aria-pressed", String(index === 0));

      button.append(
        icon(topic?.icon || "book"),
        node("span", "", topic?.name || "All policies")
      );

      button.addEventListener("click", () => {
        if (busy) return;

        document.querySelectorAll(".category-button").forEach((item) => {
          item.setAttribute("aria-pressed", String(item === button));
        });

        renderQuick(topic);

        $("question").value = topic ? topic.questions[0] : "";

        status(
          topic
            ? `Suggested question for ${topic.name}. Edit it or press Send.`
            : ""
        );

        setMenu(false, false);
        $("question").focus();
      });

      $("categories").append(button);
    });

    renderQuick(null);

    // Loading state
    function setBusy(value) {
      busy = value;
      $("question").disabled = value;

      document.querySelectorAll(
        "#submit, #clear, #copy, .quick-card, .category-button"
      ).forEach((button) => {
        button.disabled = value;
      });

      $("spinner").hidden = !value;
      $("send-icon").toggleAttribute("hidden", value);

      $("answer-panel").setAttribute("aria-busy", String(value));
    }

    // Source passages are rendered as text, never as HTML.
    function renderSources(sources) {
      $("sources").replaceChildren();
      $("source-count").textContent = String(sources.length);

      sources.forEach((source, index) => {
        const card = node("details", "source-card");

        const name = typeof source.filename === "string"
          ? source.filename.split(/[\\/]/).pop()
          : "Policy document";

        const page = source.page == null
          ? "Unknown"
          : String(source.page);

        const documentNumber = source.document_number ?? index + 1;

        card.append(
          node(
            "summary",
            "",
            `Document ${documentNumber} · ${name} · Page ${page}`
          )
        );

        card.append(
          node(
            "p",
            "",
            typeof source.content === "string"
              ? source.content
              : "No passage provided."
          )
        );

        const scores = [];

        if (Number.isFinite(source.retrieval_score)) {
          scores.push(
            `Retrieval: ${source.retrieval_score.toFixed(4)}`
          );
        }

        if (Number.isFinite(source.reranker_score)) {
          scores.push(
            `Reranker: ${source.reranker_score.toFixed(4)}`
          );
        }

        if (scores.length) {
          card.append(
            node(
              "small",
              "",
              `${scores.join(" · ")} — ranking scores, not confidence percentages.`
            )
          );
        }

        $("sources").append(card);
      });

      if (!sources.length) {
        $("sources").append(
          node(
            "p",
            "muted text-sm",
            "No source passages were returned."
          )
        );
      }
    }

    // Existing FastAPI endpoint
    $("ask-form").addEventListener("submit", async (event) => {
      event.preventDefault();

      if (busy) return;

      const question = $("question").value.trim();

      if (!question) {
        status("Please enter a question.", true);
        $("question").focus();
        return;
      }

      setBusy(true);
      lastAnswer = "";
      $("answer-panel").hidden = true;

      status("Searching policies and preparing your answer…");

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 180000);

      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question }),
          signal: controller.signal,
        });

        if (!response.ok) {
          const messages = {
            429: "The assistant is busy. Please try again shortly.",
            422: "Please check your question and try again.",
            503: "The assistant is unavailable. Please try again shortly.",
          };

          throw new Error(
            messages[response.status] ||
            `Request failed (${response.status}). Please try again.`
          );
        }

        const data = await response.json();

        if (
          typeof data.answer !== "string" ||
          !data.answer.trim() ||
          !Array.isArray(data.sources) ||
          data.sources.some(
            (source) => !source || typeof source !== "object"
          )
        ) {
          throw new Error(
            "The server returned an unexpected response."
          );
        }

        lastAnswer = data.answer;

        $("asked-question").textContent = question;
        $("answer").textContent = lastAnswer;

        $("answer-meta").textContent =
          Number.isFinite(data.elapsed_seconds)
            ? `Answered in ${data.elapsed_seconds.toFixed(1)} seconds`
            : "";

        renderSources(data.sources);

        $("answer-panel").hidden = false;

        status("Answer ready. Review the source passages below.");

        $("answer").focus({ preventScroll: true });

        $("answer-panel").scrollIntoView({
          behavior: "auto",
          block: "start",
        });
      } catch (error) {
        let message;

        if (error.name === "AbortError") {
          message =
            "The request timed out. The server may still be processing; wait before retrying.";
        } else if (error instanceof TypeError) {
          message =
            "Could not reach the server. Check your connection and try again.";
        } else {
          message = error.message;
        }

        status(message, true);
      } finally {
        clearTimeout(timer);
        setBusy(false);
      }
    });

    // New question
    $("clear").addEventListener("click", () => {
      if (busy) return;

      lastAnswer = "";

      $("question").value = "";
      $("answer-panel").hidden = true;
      $("answer").textContent = "";
      $("sources").replaceChildren();

      status("");
      $("question").focus();
    });

    // Clipboard
    $("copy").addEventListener("click", async () => {
      if (!lastAnswer || busy) return;

      try {
        await navigator.clipboard.writeText(lastAnswer);
        status("Answer copied.");
      } catch {
        status(
          "Copy is unavailable here. Select the answer text and copy it manually.",
          true
        );
      }
    });

    // Help
    $("guide-button").addEventListener("click", () => {
      setMenu(false);
      $("guide").showModal();
    });
  }, { once: true });
})();