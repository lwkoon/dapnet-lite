<template>
	<div class="chart-box"><canvas ref="canvas"></canvas></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { Chart, ArcElement, DoughnutController, Legend, Tooltip } from 'chart.js';

Chart.register(ArcElement, DoughnutController, Legend, Tooltip);

// labels/values/colors are plain arrays; colors are CSS colours.
const props = defineProps({ labels: Array, values: Array, colors: Array });
const canvas = ref(null);
let chart = null;

function render() {
	const data = {
		labels: props.labels,
		datasets: [{ data: props.values, backgroundColor: props.colors, borderWidth: 1 }]
	};
	if (chart) {
		chart.data = data;
		chart.update();
		return;
	}
	chart = new Chart(canvas.value, {
		type: 'doughnut',
		data,
		options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
	});
}

onMounted(render);
watch(() => [props.labels, props.values], render, { deep: true });
onBeforeUnmount(() => chart && chart.destroy());
</script>
