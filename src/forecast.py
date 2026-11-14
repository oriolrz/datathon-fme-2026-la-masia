"""Baselines causals de demanda neta, sense CSV ni E/S en inferència.

Contracte acordat: forecast_net_load(obs, H)[k] prediu kW a timestamp+k hores.
Inclou l'hora actual: t…t+H-1, hores cronològiques, no files del simulador.
Els vectors oficials de preu/CO₂ també inclouen t, però poden travessar buits:
només es poden emparellar per posició si són hores consecutives verificades.

Cada episodi ha de tenir un NetLoadForecaster propi. La funció pública usa
una instància de mòdul: crideu reset_forecast() abans de cada simulació.
La primera crida sempre ignora la telemetria, perquè el motor pot revelar
la demanda/solar de l'hora actual. A partir de la segona crida, el payload
correspon al timestamp de la decisió anterior, també quan hi ha un salt.
"""

from datetime import datetime, timedelta, timezone
from math import isfinite
from operator import index
from statistics import median


# Paràmetres de C fixats abans de comparar la validació; no s'optimitzen.
RECENT_HOURS = 3
HALF_LIFE_HOURS = 6.0
RESIDUAL_CLIP_QUANTILE = 0.95

# BEGIN TRAINED PARAMETERS — regenerat només amb setembre–febrer.
TRAINED_PARAMETERS = {'weekly': ((751.0,
             751.0,
             751.0,
             751.0,
             751.0,
             751.0,
             1138.75,
             1283.416667,
             1394.239167,
             1487.47,
             1510.6225,
             1543.480833,
             1514.749167,
             1459.7825,
             1437.054167,
             1409.349167,
             1410.234167,
             1420.325,
             1391.39,
             1318.333333,
             1214.4725,
             1056.583333,
             1026.0,
             1026.0),
            (1026.0,
             1026.0,
             1026.0,
             1026.0,
             1026.0,
             1026.0,
             1161.0,
             1298.5,
             1378.264167,
             1417.221667,
             1455.096667,
             1432.2475,
             1420.713333,
             1424.319167,
             1412.27,
             1380.781667,
             1443.125,
             1432.270833,
             1386.131667,
             1311.8925,
             1203.666667,
             1067.166667,
             1018.25,
             1018.0),
            (1044.0,
             1044.0,
             1044.0,
             1044.0,
             1044.0,
             1044.0,
             1162.916667,
             1296.985,
             1386.8,
             1421.185,
             1451.221667,
             1438.46,
             1428.388333,
             1382.100833,
             1402.06,
             1374.731667,
             1405.9475,
             1428.705833,
             1376.25,
             1303.166667,
             1228.666667,
             1089.583333,
             1040.166667,
             1041.0),
            (1041.0,
             1041.0,
             1041.0,
             1041.0,
             1041.0,
             1041.0,
             1151.25,
             1287.25,
             1390.736667,
             1439.948333,
             1513.0975,
             1520.095833,
             1504.184167,
             1451.020833,
             1408.555833,
             1381.8,
             1400.9925,
             1449.11,
             1390.0,
             1338.25,
             1195.333333,
             1080.666667,
             1054.083333,
             1054.0),
            (1054.0,
             1054.0,
             1054.0,
             1054.0,
             1054.0,
             1054.0,
             1136.25,
             1262.333333,
             1336.82,
             1377.151667,
             1411.266667,
             1362.279167,
             1320.161667,
             1368.085833,
             1300.301667,
             1283.725,
             1275.706667,
             1316.494167,
             1291.1325,
             1238.25,
             1172.666667,
             1073.25,
             1039.416667,
             1039.0),
            (1038.0,
             1038.0,
             1038.0,
             1038.0,
             1038.0,
             1038.0,
             844.208333,
             825.141667,
             802.34375,
             755.694167,
             674.05125,
             704.350833,
             666.442083,
             638.811667,
             669.50875,
             682.30375,
             718.829167,
             751.0525,
             807.74,
             817.375,
             808.708333,
             788.541667,
             776.625,
             776.5),
            (771.0,
             771.0,
             771.0,
             771.0,
             771.0,
             771.0,
             747.333333,
             752.833333,
             724.699167,
             670.968333,
             656.551667,
             651.814167,
             623.2775,
             602.313333,
             609.326667,
             646.356667,
             701.510833,
             745.870833,
             813.321667,
             806.333333,
             792.333333,
             769.833333,
             750.75,
             751.0)),
 'global': 1072.166667,
 'residual_clip': 335.195833,
 'train_hours': 2784,
 'train_start': '2025-09-01',
 'train_end_exclusive': '2026-03-01',
 'train_target_sha256': '983c2625463295130880f2f03118c405fc3389a195c91346c118fe8c1980c8eb',
 'cell_count_min': 15,
 'cell_count_max': 17}
DEFAULT_METHOD = "C"
# END TRAINED PARAMETERS


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def _timestamp(value):
    if isinstance(value, datetime):
        # NaT de pandas també es pot presentar com un datetime.
        try:
            return value if isfinite(value.timestamp()) else None
        except (TypeError, ValueError, OverflowError, OSError):
            return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _add_hours(ts, hours):
    if ts.utcoffset() is not None:
        return (ts.astimezone(timezone.utc) + timedelta(hours=hours)).astimezone(ts.tzinfo)
    return ts + timedelta(hours=hours)


def _elapsed_hours(later, earlier):
    if (later.utcoffset() is None) != (earlier.utcoffset() is None):
        return None
    if later.utcoffset() is not None:
        later, earlier = later.astimezone(timezone.utc), earlier.astimezone(timezone.utc)
    return (later - earlier).total_seconds() / 3600.0


def _calendar(obs):
    """Fallback si falta timestamp: només accepta hora i dia coherents."""
    try:
        hour, weekday = index(obs.get("hour")), index(obs.get("day_of_week"))
    except TypeError:
        return None
    if 0 <= hour < 24 and 0 <= weekday < 7:
        return weekday, hour
    return None


class NetLoadForecaster:
    """A: persistència; B: mediana setmanal; C: B + residu recent amortit.

    La instància és seqüencial i independent d'altres agents. Repetir el mateix
    timestamp és idempotent. Un retrocés temporal inicia un episodi nou;
    dos episodis amb el mateix timestamp inicial requereixen reset explícit.
    """

    def __init__(self, method=None, parameters=None):
        self.method = DEFAULT_METHOD if method is None else method
        if self.method not in ("A", "B", "C"):
            raise ValueError("method ha de ser A, B o C")
        parameters = TRAINED_PARAMETERS if parameters is None else parameters
        self.weekly = tuple(tuple(float(v) for v in row) for row in parameters["weekly"])
        self.global_median = float(parameters["global"])
        self.residual_clip = float(parameters["residual_clip"])
        values = [v for row in self.weekly for v in row]
        if len(self.weekly) != 7 or any(len(row) != 24 for row in self.weekly):
            raise ValueError("Cal un perfil de 7 dies × 24 hores")
        if not all(isfinite(v) for v in values + [self.global_median, self.residual_clip]):
            raise ValueError("Els paràmetres han de ser finits")
        if self.residual_clip < 0 or parameters.get("train_hours", 0) <= 0:
            raise ValueError("Calen paràmetres entrenats i un límit residual no negatiu")
        self.reset()

    def reset(self):
        self._previous = None
        self._last_net = None
        self._recent = []

    def _profile(self, ts):
        return self.weekly[ts.weekday()][ts.hour]

    def _observe(self, obs, ts):
        if self._previous is None:
            self._previous = ts
            return
        delta = _elapsed_hours(ts, self._previous)
        if delta == 0:
            return
        if delta is None or delta < 0:
            self.reset()
            self._previous = ts
            return
        source = self._previous
        if delta != 1:
            self._recent = []
        telemetry = obs.get("noves_dades_5min")
        if isinstance(telemetry, dict):
            load = _finite(telemetry.get("ultim_consum_kw"))
            solar = _finite(telemetry.get("ultima_solar_kw"))
            if load is not None and solar is not None and load >= 0 and solar >= 0:
                net = load - solar
                if isfinite(net):
                    self._last_net = net
                    # No traslladar a l'hora anterior una mesura de fa una setmana.
                    if delta == 1:
                        residual = net - self._profile(source)
                        residual = max(-self.residual_clip, min(self.residual_clip, residual))
                        self._recent.append((source, residual))
        self._previous = ts
        self._recent = [
            (when, value) for when, value in self._recent
            if 0 < _elapsed_hours(ts, when) <= RECENT_HOURS
        ]

    def forecast(self, obs: dict, horizon: int = 24) -> list[float]:
        if isinstance(horizon, bool):
            raise ValueError("horizon ha de ser un enter no negatiu")
        try:
            horizon = index(horizon)
        except TypeError as exc:
            raise ValueError("horizon ha de ser un enter no negatiu") from exc
        if horizon < 0:
            raise ValueError("horizon ha de ser un enter no negatiu")
        if horizon == 0:
            return []
        obs = obs if isinstance(obs, dict) else {}
        ts = _timestamp(obs.get("timestamp"))
        if ts is None:
            # Una crida sense rellotge trenca l'atribució del payload de la següent.
            self.reset()
            calendar = _calendar(obs)
            if self.method == "A" or calendar is None:
                return [self.global_median] * horizon
            weekday, hour = calendar
            return [self.weekly[((weekday * 24 + hour + h) // 24) % 7][(hour + h) % 24]
                    for h in range(horizon)]
        self._observe(obs, ts)
        if self.method == "A":
            value = self.global_median if self._last_net is None else self._last_net
            return [float(value)] * horizon
        residual = median([value for _, value in self._recent]) if self._recent else 0.0
        age = _elapsed_hours(ts, self._recent[-1][0]) if self._recent else 0.0
        output = []
        for h in range(horizon):
            value = self._profile(_add_hours(ts, h))
            if self.method == "C":
                value += residual * 2.0 ** (-(age + h) / HALF_LIFE_HOURS)
            output.append(float(value))
        return output


# Creació mandrosa: importar el mòdul no entrena ni obre cap fitxer.
_default_forecaster = None


def reset_forecast():
    """Cridar a l'inici de cada episodi si s'utilitza la funció de mòdul."""
    global _default_forecaster
    _default_forecaster = None


def forecast_net_load(obs: dict, horizon: int = 24) -> list[float]:
    """Prediu t…t+horizon-1; kW nets, longitud exacta i valors finits.

    Necessita crides cronològiques a cada pas, inclosos els no puntuats. Per
    executar dos agents intercalats, utilitzeu una instància pròpia per agent.
    """
    global _default_forecaster
    if _default_forecaster is None:
        _default_forecaster = NetLoadForecaster()
    return _default_forecaster.forecast(obs, horizon)
