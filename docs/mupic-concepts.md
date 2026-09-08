# Concepts

## Elements
Everything on the image is an `element` - a drawable piece of text or an image.
Even the complete image is a special element called the `output`.

## Bounding boxes (bbox)
_Note_ : The box model is different from that in html.

An element is composed of up to 4 different bounding boxes.
From outside in they are:

1. full
2. margin - optional
3. border - optional
4. content

Margin and border bboxes only exist if the corresponding decoration is configured.

The `full` bbox is always present and represents the full extent of the element.

The `margin` bbox is present if a margin is configured for the element. 
It represents the outside edge of the margin. Each side of the margin can be addressed
individually to place elements.
It is equal to the `full` box.

The `border` bbox is present if a border is configured for the element.
It represents the outside edge ofthe border. Like margin, each side of the border
can be address individually to place elements. Unlike margin however, not all sides
need be present.

The `content` bbox is always present and is what is left over after margin and border
are subtracted. This represents the outside edge of the content.

## Address Triple

The `address triple` is how particular places on the image are targetted to place elements.
In full form the triple is:

`Element`.`BBox`.`Piece`

### Element
The name of an element that has already been defined. The special element name 
`output` may be used to address the image as a whole.

The element named in the triple is the _target element_. The element
being configured is the _client element_.

The element name can be double-quoted if the name contains space or
other special characters.

`"My Cool Element".border.left`

### BBox
One of the [bounding boxes](#bounding-boxes-bbox) defined for the target element. 
If the bbox does not exist (e.g. a margin has not been defined on the target 
element, so margin bbox does not exist), an error will be raised.

### Piece

`Margin` and `border` are made of up to 4 overlapping pieces - left, right, top, bottom.
Those words are used to narraw the target to just one of the pieces.

For `content` and `full` bboxes, pieces do not exist and the _piece_ word and 
the separator dot are left off.

## Z-Order

`Z-Order` is a measure of which elements are "in front of" or "behind"
another. Elements that are in front (higher z-order) will be drawn over and
obscure those elements that have lower z-order.

Normally, elements are placed on the image in the order they 
are defined in the file. Later elements in the file will be on top of elements
earlier in the list.

The exception to this is the special `output` element. It is placed first on
the image regardless of where the definition is in the file.

The z-order can be changed by specifying a number in the configuration. This
allows you to define an element early - to use as a target element for position -
but render it later. A z-order number may be either a positive or negative integer.

If two elements wind up with the same configure z-order, then their relative place
in the list will be used as a tie-breaker.

The default z-order is 0.

## Positioning

Elements are always positioned with respect to other elements. Even when placing
on the full image, the `output` pseudo-element is used for positioning.

There are 4 ways to position - a simple syntax, attach syntax, overlay
syntax, and relative syntax.

All element types have a `position` specifier that must be present in the 
configuration.

### Simple syntax

`Width`-`Height`-`offset`

Width and Height are both one of `min`, `mid`, `max`. The _target element_ is
always `output`.

Internally, this is rewritten as :
```
overlay(output.content, width, height, width, height, offset)
```

### Attach Syntax

```
attach(triple, side, position [, anchor] [, offset])
```

Designed to easily "attach" an element to another so they move as a unit
if the _target element_ is repositioned.

Looking at the [imge_fit test config file](../tests/image_fit.mupic), notice how
the elements to right in a line are attached to the left most element.

### triple
An [address triple](#address-triple). Several shortcuts are implemented.

`element` becomes `element.full`

`border.piece` becomes `cover.border.piece`

### side
Which side of the target bbox is the client element to be attached.

One of `left`, `right`, `top`, or `bottom`.

This also sets the relationship between the two elements. for instance, `left`
also means that the client element will be to the left of the target element. 
So, the _right_ side of the client element will be used as the anchor.

This is __not__ the same as the _piece_ part of the address triple.

An attach call like :
```
attach(my_element.border.top, bottom ...)
```
is valid and requests that the client element be placed below the top border piece.

### position
Where along the requested side to place the client element. This can be specified
as :

- A keyword - one of `min`, `mid`, `max`.
- A percentage - e.g. `20%`. This can be less than zero and greater than 100%
  if required. These will place the attach point off of the actual target element
  line. The percentage is relative to the size of the _target element_.
- A pixel amount using `px` - e.g. `20px` . this is counted based on the far left
  or top of the target element.

  A plain number is considered a `px` distance.

`min` is equivalent to `0%`. `mid` is equivalent to `50%`. `max` is equivalent 
to `100%`.

### anchor
Where along the corresponding client element side to attach. Specify one of
`min`, `mid`, `max`.

If anchor is not given, a default is chosen based on the `position` value.

If `position` is a percentage and is less than `30%` then anchor is 'min'.

If `position` is a percentage and is < `70%` and >= `30%` then anchor is 'mid'.

If `position` is a percentage and is and >= `70%` then anchor is 'mid'.

If `position` is a keyword, the same keyword is used for anchor.

Otherwise, anchor is set to `min`


### offset
Control the off-axis distance.

`position` and `anchor` work together to defined the on-axis placement of the client
element (`x` for `top`, `bottom`; `y` for `left`, `right`).

`offset` allows you fine-tune the relative distance on the other off-axis direction.

By default, the `offset` is 0 and the anchor point will be directly on the attach point.

`offset` is an integer that may be positive or negative. Positive offsets move the
client _away_ from the target. Negative offset move the client _towards_ the
target.

## Overlay syntax

Designed to easily place elements inside other elements. However,
with the flexible positioning, elements can be placed partially inside
another.

```
overlay(triple, side, x_pos, y_pos [, x_anchor, y_anchor] [, offset])
```


### triple
An [address triple](#address-triple). Several shortcuts are implemented.

`element` becomes `element.content`

`border.piece` becomes `cover.border.piece`

### position
Where inside the targe element to place the client element. Both positions can
be specified as:

- A keyword - one of `min`, `mid`, `max`.
- A percentage - e.g. `20%`. This can be less than zero and greater than 100%
  if required. These will place the attach point outside  the target element
  The percentage is relative to the size of the _target element_ in that direction.
- A pixel amount using `px` - e.g. `20px` . this is counted based on the far left
  or top of the target element.

  A plain number is considered a `px` distance.

`min` is equivalent to `0%`. `mid` is equivalent to `50%`. `max` is equivalent 
to `100%`.


### anchor
Where inside the client element to attach. Specify one of
`min`, `mid`, `max`.

If anchor is not given, a default is chosen based on the `position` value.

If `position` is a percentage and is less than `30%` then anchor is 'min'.

If `position` is a percentage and is < `70%` and >= `30%` then anchor is 'mid'.

If `position` is a percentage and is and >= `70%` then anchor is 'mid'.

If `position` is a keyword, the same keyword is used for anchor.

Otherwise, anchor is set to `min`

### offset

The software will make sure that the client element is at least offset pixels
away from the walls of the target element.

The offset may only be positive (or 0)

The offset is only active if one of the key words were used to specify the placement
in a given direction.

```
# The far end of the client element will be at least 20 pixels away from the
# the two walls of the cover element.
position = "overlay(cover, max, max, max, max, 20)"
```

## Output Syntax

This is a specialized form of the `overlay` syntax to address a common
situation - placing an element relative to the output.

```
output(x_pos, y_pos, [, x_anchor, y_anchor] [, offset])
```

This is internally transformed to :
```
overlay(output.content, x_pos, y_pos, [, x_anchor, y_anchor] [, offset])
```

## Relative Syntax

Similar to `overlay` but makes the offset more powerful.

```
relative(triple, side, x_pos, y_pos [, x_anchor, y_anchor] [, offset_x, offset_y])
r(triple, side, x_pos, y_pos [, x_anchor, y_anchor] [, offset_x, offset_y])
```
### triple
An [address triple](#address-triple). Several shortcuts are implemented.

`element` becomes `element.content`

`border.piece` becomes `cover.border.piece`

### position
Where inside the targe element to place the client element. Both positions can
be specified as:

- A keyword - one of `min`, `mid`, `max`.
- A percentage - e.g. `20%`. This can be less than zero and greater than 100%
  if required. These will place the attach point outside  the target element
  The percentage is relative to the size of the _target element_ in that direction.
- A pixel amount using `px` - e.g. `20px` . this is counted based on the far left
  or top of the target element.

  A plain number is considered a `px` distance.

`min` is equivalent to `0%`. `mid` is equivalent to `50%`. `max` is equivalent 
to `100%`.


### anchor
Where inside the client element to attach. Specify one of
`min`, `mid`, `max`.

If anchor is not given, a default is chosen based on the `position` value.

If `position` is a percentage and is less than `30%` then anchor is 'min'.

If `position` is a percentage and is < `70%` and >= `30%` then anchor is 'mid'.

If `position` is a percentage and is and >= `70%` then anchor is 'mid'.

If `position` is a keyword, the same keyword is used for anchor.

Otherwise, anchor is set to `min`

### offset

A pair of integers that allow you to offset that many pixels. The offset values
are directly added to the coordinates.
