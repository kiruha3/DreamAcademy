<template>
  <div>
    <section class="hero">
      <div class="container">
        <h1>Академия DreamDocs</h1>
        <p>Обучайтесь работе с нашими продуктами. Сертификация, тестирование и поддержка экспертов.</p>
        <router-link to="/courses" class="btn-primary btn-large">Начать обучение</router-link>
      </div>
    </section>

    <section class="features">
      <div class="container">
        <h2>Почему Академия DreamDocs?</h2>
        <div class="features-grid">
          <div class="feature">
            <h3>Интерактивные курсы</h3>
            <p>Изучайте продукты по модулям с видео, текстами и практикой.</p>
          </div>
          <div class="feature">
            <h3>Проверка знаний</h3>
            <p>Автотесты + проверка специалистами для уверенности в навыках.</p>
          </div>
          <div class="feature">
            <h3>Сертификация</h3>
            <p>Подтвердите компетенции и покажите результат партнерам.</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: #fff;
  padding: 100px 0;
  text-align: center;
}
.hero h1 { font-size: 48px; margin-bottom: 16px; }
.hero p { font-size: 20px; max-width: 600px; margin: 0 auto 32px; opacity: 0.95; }

.features { padding: 80px 0; background: var(--color-bg-light); }
.features h2 { text-align: center; font-size: 36px; color: var(--color-dark); margin-bottom: 48px; }
.features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 24px; }
.feature { background: #fff; padding: 24px; border-radius: 12px; }
.feature h3 { color: var(--color-dark); margin-bottom: 8px; }
</style>
