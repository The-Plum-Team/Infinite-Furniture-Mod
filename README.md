# Infinite Furniture

Furniture that grows. For now there is one piece, the **wardrobe**, and wardrobes join together:

| Place a wardrobe…                                      | and you get                          |
| ------------------------------------------------------ | ------------------------------------ |
| on its own                                             | a small wardrobe with a drawer       |
| on top of (or under) a small one                       | a tall wardrobe with a hinged door   |
| against the left or right side of a small one          | a wide wardrobe with two drawers     |
| so it completes a 2x2 square of wardrobes              | a big two-door wardrobe              |

- Hold a wardrobe and look at another one: a see-through preview shows the wardrobe the click
  will build. Fronts and backs never join, and every piece must face the same way.
- Every wardrobe is a chest: 27 slots for the small one, 54 for the others. Joining keeps
  everything inside; whatever doesn't fit drops on the floor.
- The clothes inside fill up as you put things in.
- Breaking any block of a wardrobe takes the whole wardrobe down and gives back one wardrobe per
  block, with its contents.

Crafting: three planks on top, a plank, a chest and a plank in the middle, and two sticks for the
legs.

## Loaders

Minecraft 1.20.1 on Fabric (with Fabric API) and Forge. It needs
[Architectury API](https://modrinth.com/mod/architectury-api) and
[GeckoLib](https://modrinth.com/mod/geckolib) 4.

## Building

```sh
./gradlew build              # fabric/build/libs and forge/build/libs
./gradlew :fabric:runShowcase  # development: builds every wardrobe in a test world and photographs it
```

Gradle runs on Java 21; the mod targets Java 17.

## Models

The wardrobes are drawn in Blockbench. `art/wardrobe/*.bbmodel` are the sources, made by the
scripts in `art/wardrobe/generator/`. `python3 tools/convert_models.py` turns them into the
GeckoLib geometry, animations and textures under `common/src/main/resources`, plus the item model;
`--check` tells whether those are up to date.
