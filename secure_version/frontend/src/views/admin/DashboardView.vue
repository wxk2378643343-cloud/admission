<script setup>
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { request } from '../../api'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer
])

const stats = ref({
  student_count: 0,
  plan_count: 0,
  admission_count: 0,
  notice_count: 0
})
const chartData = ref({
  status: [],
  results: [],
  majors: [],
  scores: [],
  latest_notices: [],
  tasks: {}
})
const statusChartRef = ref(null)
const majorChartRef = ref(null)
const scoreChartRef = ref(null)
const charts = []

function initChart(el, option) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
}

function renderCharts() {
  charts.splice(0).forEach((chart) => chart.dispose())

  initChart(statusChartRef.value, {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#6a788d' } },
    series: [
      {
        name: '状态占比',
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['50%', '44%'],
        data: chartData.value.status.length ? chartData.value.status : chartData.value.results,
        label: { formatter: '{b}' }
      }
    ]
  })

  initChart(majorChartRef.value, {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 36, right: 18, top: 48, bottom: 36 },
    xAxis: {
      type: 'category',
      data: chartData.value.majors.map((item) => item.major),
      axisLabel: { color: '#6a788d' }
    },
    yAxis: { type: 'value', axisLabel: { color: '#6a788d' } },
    series: [
      {
        name: '计划人数',
        type: 'bar',
        data: chartData.value.majors.map((item) => item.quota),
        itemStyle: { color: '#2f7de1', borderRadius: [8, 8, 0, 0] }
      },
      {
        name: '已录取',
        type: 'bar',
        data: chartData.value.majors.map((item) => item.admitted),
        itemStyle: { color: '#18b9c8', borderRadius: [8, 8, 0, 0] }
      }
    ]
  })

  initChart(scoreChartRef.value, {
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 18, top: 24, bottom: 34 },
    xAxis: {
      type: 'category',
      data: chartData.value.scores.map((item) => item.name),
      axisLabel: { color: '#6a788d' }
    },
    yAxis: { type: 'value', axisLabel: { color: '#6a788d' } },
    series: [
      {
        name: '学生人数',
        type: 'line',
        smooth: true,
        symbolSize: 9,
        areaStyle: { color: 'rgba(24, 185, 200, 0.14)' },
        lineStyle: { width: 4, color: '#18b9c8' },
        itemStyle: { color: '#18b9c8' },
        data: chartData.value.scores.map((item) => item.value)
      }
    ]
  })
}

function resizeCharts() {
  charts.forEach((chart) => chart.resize())
}

onMounted(async () => {
  stats.value = await request('/admin/stats')
  chartData.value = await request('/admin/dashboard/charts')
  await nextTick()
  renderCharts()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  charts.splice(0).forEach((chart) => chart.dispose())
})
</script>

<template>
  <div class="dashboard-hero">
    <div>
      <div class="eyebrow">Today Overview</div>
      <h3>招生工作台</h3>
      <p>快速查看核心业务规模，进入左侧模块完成增删改查和信息发布。</p>
    </div>
    <div class="hero-chip">2026 招生季</div>
  </div>

  <div class="cards">
    <div class="card accent-blue">
      <span>学生总数</span>
      <strong>{{ stats.student_count }}</strong>
      <em>已建档考生</em>
    </div>
    <div class="card accent-green">
      <span>招生计划</span>
      <strong>{{ stats.plan_count }}</strong>
      <em>专业批次</em>
    </div>
    <div class="card accent-orange">
      <span>录取记录</span>
      <strong>{{ stats.admission_count }}</strong>
      <em>结果数据</em>
    </div>
    <div class="card accent-red">
      <span>公告数量</span>
      <strong>{{ stats.notice_count }}</strong>
      <em>已发布通知</em>
    </div>
  </div>

  <div class="dashboard-grid">
    <div class="panel chart-panel">
      <div class="panel-head">
        <div>
          <div class="eyebrow">Admission Status</div>
          <h3>录取状态占比</h3>
        </div>
      </div>
      <div ref="statusChartRef" class="chart-box"></div>
    </div>

    <div class="panel chart-panel wide">
      <div class="panel-head">
        <div>
          <div class="eyebrow">Major Capacity</div>
          <h3>各专业计划与录取</h3>
        </div>
      </div>
      <div ref="majorChartRef" class="chart-box"></div>
    </div>

    <div class="panel chart-panel">
      <div class="panel-head">
        <div>
          <div class="eyebrow">Score Range</div>
          <h3>成绩分布</h3>
        </div>
      </div>
      <div ref="scoreChartRef" class="chart-box small"></div>
    </div>

    <div class="panel task-panel">
      <div class="panel-head">
        <div>
          <div class="eyebrow">Todo</div>
          <h3>待处理事项</h3>
        </div>
      </div>
      <div class="task-list">
        <div>
          <span>待审核/待录取学生</span>
          <strong>{{ chartData.tasks.pending_students || 0 }}</strong>
        </div>
        <div>
          <span>未发布录取结果</span>
          <strong>{{ chartData.tasks.unpublished_admissions || 0 }}</strong>
        </div>
        <div>
          <span>开放招生计划</span>
          <strong>{{ chartData.tasks.open_plans || 0 }}</strong>
        </div>
      </div>
    </div>

    <div class="panel notice-panel">
      <div class="panel-head">
        <div>
          <div class="eyebrow">Latest Notices</div>
          <h3>最新公告</h3>
        </div>
      </div>
      <div class="admin-notice-list">
        <div v-for="notice in chartData.latest_notices" :key="notice.id">
          <strong>{{ notice.title }}</strong>
          <span>{{ notice.created_at }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
