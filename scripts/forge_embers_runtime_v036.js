// Project Genesis / isolated forge V036. PlayCanvas classic script component.
// Attach to the root of the GLB render hierarchy after artistic approval.
// Animates ONLY three ember PBR material zones. Does not change geometry.
var ForgeEmbersFlicker = pc.createScript('forgeEmbersFlicker');

ForgeEmbersFlicker.attributes.add('baseIntensity', {
    type: 'number', default: 19.0, min: 2, max: 30,
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
        console.warn('Project Genesis V036: hotcoal material zones not found under forge root');
    }
    this.on('destroy', this.restore, this);
};

ForgeEmbersFlicker.prototype.update = function (dt) {
    this.elapsed += Math.min(Math.max(dt, 0), 0.15) * this.flickerSpeed;
    var t = this.elapsed;
    for (var i = 0; i < this.groups.length; i++) {
        var group = this.groups[i];
        var phase = group.phase;
        // No hard on/off: three overlapping frequencies resemble air-fed embers.
        var slow = 0.27 * Math.sin(t * 3.1 + phase);
        var flutter = 0.22 * Math.sin(t * 9.2 + phase * 1.3);
        var micro = 0.10 * Math.sin(t * 17.3 + phase * 0.72);
        var pulse = Math.max(0.42, Math.min(1.58, 0.94 + slow + flutter + micro));
        group.material.emissiveIntensity = this.baseIntensity * pulse;
        group.material.update();
    }
    if (this.lightBase !== null && this.lightEntity && this.lightEntity.light) {
        var lightPulse = 0.90 + 0.12 * Math.sin(t * 4.3 + 0.35)
            + 0.07 * Math.sin(t * 10.1);
        this.lightEntity.light.intensity = this.lightBase * lightPulse;
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
