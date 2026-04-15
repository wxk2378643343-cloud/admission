<template>
  <section class="card">
    <SectionHeader title="成绩管理表格">
      <template #actions>
        <button v-if="isAdmin" class="btn primary" @click="$emit('open-import')">成绩导入</button>
        <button class="btn ghost small" @click="$emit('refresh')">刷新</button>
      </template>
    </SectionHeader>
    <table class="table">
      <thead><tr><th>考生ID</th><th>姓名</th><th>准考证</th><th>语文</th><th>数学</th><th>外语</th><th>综合</th><th>总分</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="row in rows" :key="row.candidate_id">
          <td>{{ row.candidate_id }}</td>
          <td>{{ row.name }}</td>
          <td>{{ row.exam_no }}</td>
          <td>{{ row.chinese }}</td>
          <td>{{ row.math }}</td>
          <td>{{ row.foreign_language }}</td>
          <td>{{ row.comprehensive }}</td>
          <td>{{ row.total_score }}</td>
          <td>{{ row.has_score ? '已录入' : '未录入' }}</td>
          <td>
            <div class="toolbar-inline">
              <button v-if="isAdmin" class="btn ghost small" @click="$emit('edit-score', row)">编辑成绩</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import SectionHeader from './SectionHeader.vue'

defineProps({
  isAdmin: {
    type: Boolean,
    default: false
  },
  rows: {
    type: Array,
    default: () => []
  }
})

defineEmits(['open-import', 'refresh', 'edit-score'])
</script>

