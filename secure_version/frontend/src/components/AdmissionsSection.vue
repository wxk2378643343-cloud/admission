<template>
  <section class="card">
    <SectionHeader title="录取管理表格">
      <template #actions>
        <button class="btn ghost small" @click="$emit('refresh')">刷新</button>
      </template>
    </SectionHeader>
    <table class="table">
      <thead><tr><th>考生ID</th><th>姓名</th><th>准考证</th><th>全部志愿</th><th>当前录取院校</th><th>当前录取专业</th><th>状态</th><th>录取状态</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="row in rows" :key="row.candidate_id">
          <td>{{ row.candidate_id }}</td>
          <td>{{ row.name }}</td>
          <td>{{ row.exam_no }}</td>
          <td>
            <div v-if="row.choices && row.choices.length">
              <div v-for="c in row.choices" :key="c.id">
                {{ c.priority }}志愿：{{ c.university }} / {{ c.major }}
              </div>
            </div>
            <span v-else>-</span>
          </td>
          <td>{{ row.university || '-' }}</td>
          <td>{{ row.major || '-' }}</td>
          <td>{{ statusLabel(row.status) }}</td>
          <td>{{ row.status === 'admitted' ? '已录取' : '未录取' }}</td>
          <td>
            <div class="toolbar-inline" v-if="canOperate">
              <button class="btn ghost small" @click="$emit('action', row, 'pending', '拟录取', selectedChoice(row))" :disabled="isLocked(row)">拟录取</button>
              <button class="btn ghost small" @click="$emit('action', row, 'admitted', '录取', selectedChoice(row))" :disabled="isLocked(row)">录取</button>
              <button class="btn ghost small" @click="$emit('action', row, 'rejected', '拒绝')" :disabled="isLocked(row)">拒绝</button>
            </div>
            <select
              v-if="canOperate && row.choices && row.choices.length"
              class="mt8"
              @change="onChoiceChange(row, $event)"
            >
              <option v-for="c in row.choices" :key="c.id" :value="c.id">
                {{ c.priority }}志愿：{{ c.university }} / {{ c.major }}
              </option>
            </select>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { reactive } from 'vue'
import SectionHeader from './SectionHeader.vue'

defineProps({
  rows: {
    type: Array,
    default: () => []
  },
  canOperate: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refresh', 'action'])
const selectedChoiceIdMap = reactive({})

function statusLabel(status) {
  if (status === 'pending') return '拟录取'
  if (status === 'admitted') return '录取'
  if (status === 'rejected') return '拒绝'
  return '-'
}

function isLocked(row) {
  return row && row.status === 'admitted'
}

function selectedChoice(row) {
  if (!row || !row.choices || !row.choices.length) return null
  const selectedId = selectedChoiceIdMap[row.candidate_id]
  const selected = row.choices.find((c) => c.id === Number(selectedId))
  return selected || row.choices[0]
}

function onChoiceChange(row, event) {
  selectedChoiceIdMap[row.candidate_id] = Number(event.target.value)
}

</script>
