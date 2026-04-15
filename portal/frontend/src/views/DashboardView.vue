<template>
  <section class="dashboard">
    <div class="container">
      <h2>Личный кабинет</h2>
      <div class="dashboard-grid">
        <div class="card">
          <h3>Мои курсы</h3>
          <p>Список курсов появится после авторизации.</p>
        </div>
        <div class="card">
          <h3>Прогресс</h3>
          <p>Пройдено 0 из 0 модулей.</p>
        </div>
        <div class="card">
          <h3>Тесты</h3>
          <p>Нет активных проверочных работ.</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.dashboard { padding: 60px 0; background: var(--color-bg-light); min-height: 60vh; }
.dashboard h2 { text-align: center; font-size: 36px; color: var(--color-dark); margin-bottom: 48px; }
.dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 24px; }
.card { background: #fff; padding: 24px; border-radius: 12px; }
.card h3 { color: var(--color-dark); margin-bottom: 8px; }
</style>
