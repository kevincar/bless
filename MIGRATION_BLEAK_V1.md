# Migration vers Bleak v1.1.1

## Changements principaux

### 1. Structure des modules

Dans Bleak v0.22.3 :

```python
from bleak.backends.bluezdbus.characteristic import BleakGATTCharacteristicBlueZDBus
from bleak.backends.bluezdbus.service import BleakGATTServiceBlueZDBus
```

Dans Bleak v1.1.1 :

```python
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.service import BleakGATTService
```

### 2. Signatures des constructeurs

**BleakGATTCharacteristic v1.1.1 :**

```python
__init__(self, obj: Any, handle: int, uuid: str, properties: list[CharacteristicPropertyName],
         max_write_without_response_size: Callable[[], int], service: BleakGATTService)
```

**BleakGATTService v1.1.1 :**

```python
__init__(self, obj: Any, handle: int, uuid: str)
```

### 3. Modifications nécessaires

#### Pour BlueZDBus backend :

- Retirer les imports spécifiques au backend
- Utiliser les classes de base communes
- Adapter les initialisations

#### Pour CoreBluetooth backend :

- Même approche que BlueZDBus

#### Pour WinRT backend :

- Même approche que BlueZDBus

## Fichiers à modifier

1. `bless/backends/characteristic.py` - OK (utilise déjà la classe de base)
2. `bless/backends/service.py` - OK (utilise déjà la classe de base)
3. `bless/backends/bluezdbus/characteristic.py` - ⚠️ À MODIFIER
4. `bless/backends/bluezdbus/service.py` - ⚠️ À MODIFIER
5. `bless/backends/corebluetooth/characteristic.py` - ⚠️ À MODIFIER
6. `bless/backends/corebluetooth/service.py` - ⚠️ À MODIFIER
7. `bless/backends/winrt/characteristic.py` - ⚠️ À MODIFIER
8. `bless/backends/winrt/service.py` - ⚠️ À MODIFIER

## Approche

Les classes Bless héritent de BleakGATTCharacteristic/Service mais ne doivent pas appeler leur **init**
car elles construisent elles-mêmes les objets backend. Il faut donc stocker les attributs directement.
