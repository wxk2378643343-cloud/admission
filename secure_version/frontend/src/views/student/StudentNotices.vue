<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { request } from '../../api'

const route = useRoute()
const notices = ref([])
const selected = ref(null)

const selectedId = computed(() => route.query.id)

onMounted(async () => {
  notices.value = await request('/student/notices')
  if (selectedId.value) {
    selected.value = await request(`/student/notices/${selectedId.value}`)
  }
})
</script>

<template>
  <div class="student-grid">
    <div class="student-list">
      <div v-for="notice in notices" :key="notice.id" class="notice-card">
        <router-link :to="`/student/notices?id=${notice.id}`">
          <h3>{{ notice.title }}</h3>
        </router-link>
        <div class="meta">{{ notice.publisher }} · {{ notice.created_at }}</div>
        <p>{{ notice.content }}</p>
      </div>
    </div>
    <div class="student-list">
      <div class="student-card notice-detail-card">
        <div class="eyebrow">Notice Detail</div>
        <h3>公告详情</h3>
        <div v-if="selected" class="detail-box">{{ selected.content }}</div>
        <div v-else class="meta">点击左侧公告查看详情。</div>
      </div>
    </div>
  </div>
</template>
