<script setup>
import { onMounted, ref } from 'vue'
import { getCurrentUser, request } from '../../api'

const profile = ref(null)

onMounted(async () => {
  profile.value = await request(`/student/profile?user_id=${getCurrentUser().id}`)
})
</script>

<template>
  <div class="student-card feature-card">
    <div class="eyebrow">Candidate Profile</div>
    <h3>个人信息</h3>
    <div v-if="profile" class="detail-box">
      <div class="info-list two-col">
        <span>学号：{{ profile.student_no }}</span>
        <span>姓名：{{ profile.name }}</span>
        <span>性别：{{ profile.gender }}</span>
        <span>成绩：{{ profile.score }}</span>
        <span>专业：{{ profile.major }}</span>
        <span>志愿：{{ profile.choice_major }}</span>
        <span>当前状态：{{ profile.status }}</span>
      </div>
    </div>
  </div>
</template>
