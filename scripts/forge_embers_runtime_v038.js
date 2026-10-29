// Project Genesis / isolated forge V038. PlayCanvas classic script component.
// Attach to the root of the GLB render hierarchy after artistic approval.
// Animates ONLY three ember PBR material zones. Does not change geometry.
var ForgeEmbersFlicker = pc.createScript('forgeEmbersFlicker');

ForgeEmbersFlicker.attributes.add('baseIntensity', {
    type: 'number', default: 28.0, min: 2, max: 30,
    title: 'Emissive intensity'
});
ForgeEmbersFlicker.attributes.add('flickerSpeed', {
    type: 'number', default: 1.0, min: 0.1, max: 4,
    title: 'Flicker speed'
});
ForgeEmbersFlicker.attributes.add('lightEntity', {
    type: 'entity', title: 'Optional ember point light'
});

ForgeEmbersFlicker.prototype.initialize = function () {
    this.elapsed = 0;
    this.groups = [];
    this.previous = [];
    this.lightBase = this.lightEntity && this.lightEntity.light ?
        this.lightEntity.light.intensity : null;
    var matches = new Map();
    var renderComponents = this.entity.findComponents('render');
    for (var r = 0; r < renderComponents.length; r++) {
        var instances = renderComponents[r].meshInstances;
        for (var m = 0; m < instances.length; m++) {
            var meshInstance = instances[m];
            var source = meshInstance.material;
            if (!source || source.name.indexOf('forge_cracked_hot_charcoal_ember_map') < 0) continue;
            var assigned = matches.get(source);
            if (!assigned) {
                // Cloning prevents a shared material from affecting other forge instances.
                var copy = source.clone();
                copy.name = source.name + '_animated';
                assigned = { material: copy, phase: this.groups.length * 2.1 };
                matches.set(source, assigned);
                this.groups.push(assigned);
            }
            this.previous.push({ meshInstance: meshInstance, material: source });
            meshInstance.material = assigned.material;
        }
    }
    if (!this.groups.length) {
        console.warn('Project Genesis V038: hotcoal material zones not found under forge root');
    }
    this.on('destroy', this.restore, this);
};

// Coal breathes in a synchronized 4-second rise and fall. No fast flutter.
// 0.68 -> 1.32 -> 0.68 with zero speed at each turning point.
ForgeEmbersFlicker.prototype.update = function (dt) {
    this.elapsed += Math.max(dt, 0) * this.flickerSpeed;
    var heat = 0.5 - 0.5 * Math.cos(this.elapsed * Math.PI * 0.5);
    var pulse = 0.68 + 0.64 * heat;
    for (var i = 0; i < this.groups.length; i++) {
        this.groups[i].material.emissiveIntensity = this.baseIntensity * pulse;
        this.groups[i].material.update();
    }
    if (this.lightBase !== null && this.lightEntity && this.lightEntity.light) {
        this.lightEntity.light.intensity = this.lightBase * pulse;
    }
};

ForgeEmbersFlicker.prototype.restore = function () {
    for (var i = 0; i < this.previous.length; i++) {
        this.previous[i].meshInstance.material = this.previous[i].material;
    }
    for (var j = 0; j < this.groups.length; j++) {
        this.groups[j].material.destroy();
    }
    if (this.lightBase !== null && this.lightEntity && this.lightEntity.light) {
        this.lightEntity.light.intensity = this.lightBase;
    }
    this.previous = [];
    this.groups = [];
};
