<script setup>
import { onMounted, ref } from 'vue'
import { getCurrentUser, request } from '../../api'

const user = getCurrentUser()
const profile = ref(null)
const admission = ref(null)
const notices = ref([])

onMounted(async () => {
  profile.value = await request(`/student/profile?user_id=${user.id}`)
  admission.value = await request(`/student/admission?user_id=${user.id}`)
  notices.value = await request('/student/notices')
})
</script>

<template>
  <div class="student-portal-strip">
    <div class="progress-card">
      <div class="card-title-row">
        <div>
          <div class="eyebrow">Admission Timeline</div>
          <h3>招生办理进度</h3>
        </div>
        <span class="status-dot">{{ profile?.status || '待同步' }}</span>
      </div>
      <div class="timeline-steps">
        <div class="active">
          <strong>1</strong>
          <span>信息确认</span>
        </div>
        <div class="active">
          <strong>2</strong>
          <span>成绩发布</span>
        </div>
        <div :class="{ active: admission }">
          <strong>3</strong>
          <span>录取查询</span>
        </div>
        <div :class="{ active: admission?.publish_status === '已发布' }">
          <strong>4</strong>
          <span>结果发布</span>
        </div>
      </div>
    </div>

    <div class="quick-links">
      <router-link to="/student/profile">我的信息</router-link>
      <router-link to="/student/score">我的成绩</router-link>
      <router-link to="/student/choices">我的志愿</router-link>
      <router-link to="/student/admission">录取结果</router-link>
      <router-link to="/student/notices">公告通知</router-link>
    </div>
  </div>

  <div class="student-grid">
    <div class="student-list">
      <div class="student-card profile-summary">
        <div class="card-title-row">
          <div>
            <div class="eyebrow">Profile</div>
            <h3>个人概览</h3>
          </div>
          <router-link class="text-link" to="/student/profile">查看详情</router-link>
        </div>
        <div v-if="profile" class="detail-box">
          <div class="score-tile">
            <span>高考成绩</span>
            <strong>{{ profile.score }}</strong>
          </div>
          <div class="info-list">
            <span>学号：{{ profile.student_no }}</span>
            <span>姓名：{{ profile.name }}</span>
            <span>志愿：{{ profile.choice_major }}</span>
            <span>当前状态：{{ profile.status }}</span>
          </div>
        </div>
      </div>
      <div class="student-card admission-card">
        <div class="card-title-row">
          <div>
            <div class="eyebrow">Admission</div>
            <h3>录取结果</h3>
          </div>
          <router-link class="text-link" to="/student/admission">去查询</router-link>
        </div>
        <div v-if="admission?.publish_status === '已发布'" class="detail-box">
          <div class="result-status">{{ admission.result }}</div>
          <div class="info-list">
            <span>录取专业：{{ admission.major }}</span>
            <span>发布状态：{{ admission.publish_status }}</span>
          </div>
        </div>
        <div v-else-if="admission" class="meta">录取结果尚未发布，请等待通知。</div>
        <div v-else class="meta">当前暂无录取结果。</div>
      </div>
    </div>
    <div class="student-list">
      <div class="student-card">
        <div class="card-title-row">
          <div>
            <div class="eyebrow">News</div>
            <h3>最新公告</h3>
          </div>
          <router-link class="text-link" to="/student/notices">全部</router-link>
        </div>
        <div v-for="notice in notices.slice(0, 5)" :key="notice.id" class="notice-mini">
          <router-link :to="`/student/notices?id=${notice.id}`">
            <strong>{{ notice.title }}</strong>
          </router-link>
          <div class="meta">{{ notice.created_at }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
