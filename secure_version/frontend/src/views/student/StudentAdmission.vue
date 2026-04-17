<script setup>
import { onMounted, ref } from 'vue'
import { request } from '../../api'

const admission = ref(null)

onMounted(async () => {
  admission.value = await request('/student/admission')
})
</script>

<template>
  <div class="student-card feature-card">
    <div class="card-title-row">
      <div>
        <div class="eyebrow">Result Query</div>
        <h3>录取结果查询</h3>
      </div>
      <span class="status-dot">实时</span>
    </div>
    <div v-if="admission?.publish_status === '已发布'" class="detail-box">
      <div class="result-status large">{{ admission.result }}</div>
      <div class="info-list two-col">
        <span>批次：{{ admission.batch }}</span>
        <span>学院：{{ admission.college || '暂未公布' }}</span>
        <span>专业：{{ admission.major }}</span>
        <span>发布状态：{{ admission.publish_status }}</span>
      </div>
    </div>
    <div v-else-if="admission" class="empty-state">
      录取结果尚未发布，请等待招生办公室通知。
    </div>
    <div v-else class="meta">当前暂无可查询的录取信息。</div>
  </div>
</template>
