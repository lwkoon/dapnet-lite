<template>
	<div ref="el" class="map" :class="{ 'map-small': small }"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import L from 'leaflet';
import { state } from '../store';

// markers: [{ lat, lng, color, radius, popup (html), id }]
// lines:   [[[lat, lng], [lat, lng]], ...]
// pick:    show a single draggable point and emit 'pick' on click
const props = defineProps({
	markers: { type: Array, default: () => [] },
	lines: { type: Array, default: () => [] },
	pick: { type: Object, default: null },
	small: Boolean,
	fit: { type: Boolean, default: true },
	focus: String
});
const emit = defineEmits(['pick']);

const el = ref(null);
let map = null;
let layer = null;
let pickMarker = null;

function draw() {
	if (!map) return;
	layer.clearLayers();
	const bounds = [];
	props.lines.forEach((ln) => L.polyline(ln, { color: '#6c757d', weight: 1, dashArray: '4 4' }).addTo(layer));
	props.markers.forEach((m) => {
		if (!Number.isFinite(m.lat) || !Number.isFinite(m.lng)) return;
		const mk = L.circleMarker([m.lat, m.lng], {
			radius: m.radius || 8, color: '#fff', weight: 2, fillColor: m.color || '#1f6f78', fillOpacity: 0.9
		}).addTo(layer);
		if (m.popup) mk.bindPopup(m.popup);
		if (props.focus && m.id === props.focus) {
			map.setView([m.lat, m.lng], 11);
			mk.openPopup();
		}
		bounds.push([m.lat, m.lng]);
	});
	if (props.fit && !props.focus && bounds.length) map.fitBounds(bounds, { padding: [30, 30], maxZoom: 10 });
}

function drawPick() {
	if (!map || !props.pick) return;
	const ll = [props.pick.lat || 0, props.pick.lng || 0];
	if (!pickMarker) {
		pickMarker = L.circleMarker(ll, { radius: 9, color: '#fff', weight: 2, fillColor: '#dc3545', fillOpacity: 1 }).addTo(map);
	} else {
		pickMarker.setLatLng(ll);
	}
}

onMounted(() => {
	map = L.map(el.value, { worldCopyJump: true }).setView(
		props.pick && (props.pick.lat || props.pick.lng) ? [props.pick.lat, props.pick.lng] : state.map.center,
		props.pick && (props.pick.lat || props.pick.lng) ? 10 : state.map.zoom
	);
	L.tileLayer(state.mapTiles, {
		maxZoom: 18,
		attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
	}).addTo(map);
	layer = L.layerGroup().addTo(map);
	if (props.pick) {
		map.on('click', (e) => emit('pick', { lat: +e.latlng.lat.toFixed(6), lng: +e.latlng.lng.toFixed(6) }));
		drawPick();
	}
	draw();
});

watch(() => [props.markers, props.lines], draw, { deep: true });
watch(() => props.pick, (p, old) => {
	drawPick();
	// centre once when an existing location is loaded
	if (map && p && (!old || (!old.lat && !old.lng)) && (p.lat || p.lng)) map.setView([p.lat, p.lng], 10);
}, { deep: true });

onBeforeUnmount(() => map && map.remove());
</script>
