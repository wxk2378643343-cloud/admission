<script setup>
import { onMounted, ref } from 'vue'
import { request } from '../../api'

const score = ref(null)

onMounted(async () => {
  score.value = await request('/student/score')
})
</script>

<template>
  <div class="student-card feature-card">
    <div class="card-title-row">
      <div>
        <div class="eyebrow">Score Report</div>
        <h3>我的成绩</h3>
      </div>
      <span class="status-dot">已同步</span>
    </div>

    <div v-if="score" class="score-page-grid">
      <div class="score-hero">
        <span>总成绩</span>
        <strong>{{ score.score }}</strong>
        <em>当前状态：{{ score.status }}</em>
      </div>
      <div class="info-list">
        <span>姓名：{{ score.name }}</span>
        <span>学号：{{ score.student_no }}</span>
        <span>语文：{{ score.chinese_score }}</span>
        <span>数学：{{ score.math_score }}</span>
        <span>外语：{{ score.foreign_score }}</span>
        <span>综合：{{ score.comprehensive_score }}</span>
        <span>系统排名：{{ score.rank }} / {{ score.total }}</span>
        <span>填报志愿：{{ score.choice_major }}</span>
        <span>录取专业：{{ score.major || '暂未确定' }}</span>
      </div>
    </div>
    <div v-else class="meta">暂未查询到成绩信息。</div>
  </div>
</template>
