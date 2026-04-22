<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="landing">
    <header class="nav cc-container">
      <span class="logo cc-display">Career Copilot</span>
      <nav class="nav-links">
        <RouterLink class="nav-link" to="/signin">Sign in</RouterLink>
        <RouterLink class="cc-btn cc-btn--primary nav-cta" to="/signup">Get started</RouterLink>
      </nav>
    </header>

    <main>
      <section class="hero cc-container">
        <p class="eyebrow">Your next chapter, thoughtfully guided</p>
        <h1 class="headline cc-display">
          Career clarity
          <span class="headline-soft">without the noise.</span>
        </h1>
        <p class="lede">
          A calm space to explore roles, constraints, and market reality — then walk away with a plan that feels
          grounded in <em>your</em> story, not a generic script.
        </p>
        <div class="hero-actions">
          <RouterLink class="cc-btn cc-btn--primary" to="/signup">Begin free</RouterLink>
          <RouterLink class="cc-btn cc-btn--ghost" to="/signin">I already have an account</RouterLink>
        </div>
      </section>

      <section class="mesh cc-container">
        <div class="mesh-inner">
          <article class="tile">
            <h2 class="tile-title cc-display">Listen first</h2>
            <p class="tile-body">We map where you are, what matters, and what “success” means before chasing titles.</p>
          </article>
          <article class="tile">
            <h2 class="tile-title cc-display">Evidence-backed</h2>
            <p class="tile-body">Research and signals inform the conversation — so advice stays tethered to the real market.</p>
          </article>
          <article class="tile">
            <h2 class="tile-title cc-display">Warm by design</h2>
            <p class="tile-body">No robotic pep talks — just clear language, honest trade-offs, and room to breathe.</p>
          </article>
        </div>
      </section>

      <section class="closing cc-container">
        <div class="closing-card cc-card">
          <h2 class="closing-title cc-display">Ready when you are</h2>
          <p class="closing-copy">Create an account, share a bit about your path, and open the conversation.</p>
          <RouterLink class="cc-btn cc-btn--primary" to="/signup">Create your space</RouterLink>
        </div>
      </section>
    </main>

    <footer class="footer cc-container">
      <span class="logo cc-display">Career Copilot</span>
      <span class="footer-note">Built for people rethinking what’s next.</span>
    </footer>
  </div>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: radial-gradient(120% 80% at 50% -20%, #e8f0ec 0%, transparent 50%),
    radial-gradient(80% 50% at 100% 0%, #f5ebe0 0%, transparent 45%), var(--color-canvas);
}

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1.25rem;
  padding-bottom: 1.25rem;
}

.logo {
  font-size: 1.25rem;
  color: var(--color-ink);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-link {
  color: var(--color-ink-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9375rem;
}

.nav-link:hover {
  color: var(--color-ink);
}

.nav-cta {
  text-decoration: none;
  padding: 0.5rem 1.1rem;
  font-size: 0.875rem;
}

.hero {
  padding-top: 3rem;
  padding-bottom: 4rem;
  text-align: center;
  max-width: 44rem;
}

.eyebrow {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
  margin-bottom: 1rem;
}

.headline {
  font-size: clamp(2.25rem, 5vw, 3.25rem);
  color: var(--color-ink);
  margin-bottom: 1.25rem;
}

.headline-soft {
  display: block;
  font-weight: 400;
  color: var(--color-ink-muted);
  font-style: italic;
}

.lede {
  font-size: 1.125rem;
  color: var(--color-ink-muted);
  max-width: var(--max-readable);
  margin: 0 auto 2rem;
  line-height: 1.65;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}

.hero-actions .cc-btn {
  text-decoration: none;
}

.mesh {
  padding-bottom: 4rem;
}

.mesh-inner {
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .mesh-inner {
    grid-template-columns: repeat(3, 1fr);
    gap: 1.25rem;
  }
}

.tile {
  padding: 1.5rem 1.35rem;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-soft);
}

.tile-title {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
  color: var(--color-ink);
}

.tile-body {
  font-size: 0.9375rem;
  color: var(--color-ink-muted);
  line-height: 1.55;
  margin: 0;
}

.closing {
  padding-bottom: 4rem;
}

.closing-card {
  text-align: center;
  padding: 2.5rem 1.5rem;
  max-width: 32rem;
  margin: 0 auto;
}

.closing-title {
  font-size: 1.75rem;
  margin-bottom: 0.75rem;
}

.closing-copy {
  color: var(--color-ink-muted);
  margin-bottom: 1.5rem;
}

.closing-card .cc-btn {
  text-decoration: none;
}

.footer {
  margin-top: auto;
  padding: 2rem 1.25rem 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  border-top: 1px solid var(--color-border);
}

.footer .logo {
  font-size: 1.05rem;
}

.footer-note {
  font-size: 0.8125rem;
  color: var(--color-ink-faint);
}
</style>
