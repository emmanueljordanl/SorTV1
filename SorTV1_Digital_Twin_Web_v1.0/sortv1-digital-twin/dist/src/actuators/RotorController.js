export function actuatorAuthority(twin){ return {power:Boolean(twin?.plant?.power), nEN:twin?.plant?.nEN??1, state:twin?.fw?.state??'UNKNOWN'}; }
