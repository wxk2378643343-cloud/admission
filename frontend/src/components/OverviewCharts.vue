<template>
  <section class="chart-grid">
    <article class="card">
      <h3>录取状态分布</h3>
      <div ref="admissionRef" class="chart-box"></div>
    </article>
    <article class="card">
      <h3>成绩分布</h3>
      <div ref="scoreRef" class="chart-box"></div>
    </article>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  admissionStats: {
    type: Object,
    default: () => ({ admitted: 0, pending: 0, rejected: 0, none: 0 })
  },
  scoreBuckets: {
    type: Array,
    default: () => [0, 0, 0, 0]
  }
})

const admissionRef = ref(null)
const scoreRef = ref(null)
let admissionChart = null
let scoreChart = null

function renderAdmissionChart() {
  if (!admissionRef.value) return
  if (!admissionChart) {
    admissionChart = echarts.init(admissionRef.value)
  }
  admissionChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['38%', '68%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        data: [
          { value: props.admissionStats.admitted, name: '录取' },
          { value: props.admissionStats.pending, name: '拟录取' },
          { value: props.admissionStats.rejected, name: '拒绝' },
          { value: props.admissionStats.none, name: '未处理' }
        ]
      }
    ]
  })
}

function renderScoreChart() {
  if (!scoreRef.value) return
  if (!scoreChart) {
    scoreChart = echarts.init(scoreRef.value)
  }
  scoreChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: {
      type: 'category',
      data: ['<450', '450-549', '550-649', '650+']
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        barWidth: 28,
        data: props.scoreBuckets,
        itemStyle: { color: '#2f7ee8', borderRadius: [6, 6, 0, 0] }
      }
    ]
  })
}

function renderAll() {
  renderAdmissionChart()
  renderScoreChart()
}

onMounted(async () => {
  await nextTick()
  renderAll()
  window.addEventListener('resize', renderAll)
})

watch(
  () => [props.admissionStats, props.scoreBuckets],
  () => {
    renderAll()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderAll)
  if (admissionChart) admissionChart.dispose()
  if (scoreChart) scoreChart.dispose()
})
</script>

