export class Clock { constructor(){this.now=0;this.paused=true;this.speed=1;this.accumulator=0;} advance(dt){this.now+=dt;return this.now;} }
